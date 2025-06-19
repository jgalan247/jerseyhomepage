from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json
import stripe
import qrcode
from io import BytesIO
import base64
from event_management.models import Event
from .models import Cart, CartItem, Order, OrderItem, Ticket
from .utils import send_order_confirmation_email, generate_tickets_pdf
from .utils import generate_single_ticket_pdf 


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_cart(request):
    """Get or create cart based on session"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_context(request):
    """Context processor for cart"""
    cart = get_or_create_cart(request)
    return {
        'cart': cart,
        'cart_items_count': cart.total_items
    }


@require_POST
def add_to_cart(request):
    """Add event to cart via AJAX"""
    try:
        event_id = request.POST.get('event_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        
        event = get_object_or_404(Event, id=event_id, is_active=True)
        cart = get_or_create_cart(request)
        
        # Check if event already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={'quantity': 0}
        )
        
        # Update quantity
        cart_item.quantity += quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{event.title} added to cart',
            'cart_count': cart.total_items,
            'cart_total': str(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@require_POST
def quick_add_to_cart(request):
    """HTMX endpoint for adding items to cart"""
    event_id = request.POST.get('event_id')
    event = get_object_or_404(Event, id=event_id)
    cart = get_or_create_cart(request)
    
    # Create or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        event=event,
        defaults={'quantity': 0, 'price_at_time': event.price}
    )
    cart_item.quantity += 1
    cart_item.save()
    
    # Return HTML that updates multiple parts of the page
    response = HttpResponse()
    
    # Update cart count in navbar
    response.write(f'''
        <span id="cart-count" 
              hx-swap-oob="true" 
              class="badge bg-danger">
            {cart.total_items}
        </span>
    ''')
    
    # Show success message
    response.write('''
        <div id="cart-message" 
             hx-swap-oob="true" 
             class="position-fixed top-0 end-0 p-3" 
             style="z-index: 1050;">
            <div class="toast show" role="alert">
                <div class="toast-header">
                    <strong class="me-auto">Added to Cart!</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    <a href="/booking/cart/" class="btn btn-sm btn-primary">View Cart</a>
                </div>
            </div>
        </div>
        <script>
            setTimeout(() => {
                document.getElementById('cart-message').remove();
            }, 3000);
        </script>
    ''')
    
    # Update the button that was clicked
    response.write(f'''
        <button hx-post="{request.path}" 
                hx-vals='{{"event_id": "{event_id}"}}'
                class="btn btn-success">
            <i class="fas fa-check"></i> Added - Add Another
        </button>
    ''')
    
    return response

def cart_view(request):
    """Display cart page"""
    cart = get_or_create_cart(request)
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('event').all()
    }
    return render(request, 'booking/cart.html', context)


@require_POST
def update_cart(request):
    """Update cart item quantity via AJAX"""
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity'))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity > 0:
            # Check available tickets
            available = cart_item.event.available_tickets
            if quantity > available:
                return JsonResponse({
                    'success': False,
                    'error': f'Only {available} tickets available'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
        
        # Recalculate totals
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'cart_total': str(cart.total_price),
            'item_total': str(cart_item.subtotal) if quantity > 0 else '0.00'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def remove_from_cart(request):
    """Remove item from cart via AJAX"""
    try:
        item_id = request.POST.get('item_id')
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        # Recalculate totals
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart.total_items,
            'cart_total': str(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def checkout_view(request):
    """Display checkout page"""
    cart = get_or_create_cart(request)
    
    if cart.total_items == 0:
        messages.warning(request, 'Your cart is empty')
        return redirect('event_management:event_list')
    
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('event').all(),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    # Pre-fill form if user is authenticated
    if request.user.is_authenticated:
        context['user'] = request.user
    
    return render(request, 'booking/checkout.html', context)


@require_POST
def process_payment(request):
    """Process payment with Stripe"""
    print("=== PROCESS PAYMENT CALLED ===")
    
    cart = get_or_create_cart(request)
    print(f"Cart items: {cart.total_items}")
    
    if cart.total_items == 0:
        return JsonResponse({'success': False, 'error': 'Cart is empty'})
    
    try:
        # Get form data
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone', '')
        
        print(f"Form data - Email: {email}, Name: {first_name} {last_name}")
        
        # Create order
        with transaction.atomic():
            print("Creating order...")
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                total_amount=cart.total_price,
                status='pending'
            )
            print(f"Order created: {order.order_number}")
            
            # Create order items from cart
            print("Creating order items...")
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    event=item.event,
                    quantity=item.quantity,
                    price=item.event.price  # Use event price
                )
                print(f"  - Added {item.event.title} x{item.quantity}")
            
            # Create Stripe Checkout Session
            print("Creating Stripe session...")
            line_items = []
            for item in cart.items.all():
                line_items.append({
                    'price_data': {
                        'currency': 'gbp',
                        'unit_amount': int(item.event.price * 100),  # Use event price
                        'product_data': {
                            'name': item.event.title,
                            'description': f"{item.event.venue} - {item.event.date.strftime('%d %b %Y at %H:%M')}",
                        },
                    },
                    'quantity': item.quantity,
                })
            
            # Create Stripe session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                # customer_email=email,  # Removed to prevent Link from taking over
                success_url=request.build_absolute_uri(
                    reverse('booking:order_success', kwargs={'order_number': order.order_number})
                ),
                cancel_url=request.build_absolute_uri(reverse('booking:checkout')),
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number,
                }
            )
            print(f"Stripe session created: {checkout_session.id}")
            
            # Save Stripe session ID to order
            order.stripe_session_id = checkout_session.id
            order.save()
            
            # Clear the cart after successful checkout session creation
            cart.items.all().delete()
            print("Cart cleared")
            
            # Return checkout URL for JavaScript redirect
            print(f"Redirecting to: {checkout_session.url}")
            return JsonResponse({
                'success': True,
                'checkout_url': checkout_session.url
            })
            
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        print(f"Stripe error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    except Exception as e:
        # Handle other errors
        print(f"Process payment error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred processing your payment'
        })


def order_success(request, order_number):
    """Display order success page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # AUTO-SEND EMAIL FOR TESTING
    if order.status == 'pending':
        try:
            order.status = 'confirmed'
            order.paid_at = timezone.now()
            order.save()
            
            for item in order.items.all():
                item.generate_tickets()
            
            from .utils import send_order_confirmation_email
            send_order_confirmation_email(order)
        except Exception as e:
            print(f"Email error: {e}")
    
    context = {'order': order}
    return render(request, 'booking/order_success.html', context)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    print("=== WEBHOOK CALLED ===")
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    
    # Debug info
    print(f"Payload length: {len(payload)}")
    print(f"Signature header present: {sig_header is not None}")
    print(f"Webhook secret configured: {bool(settings.STRIPE_WEBHOOK_SECRET)}")
    print(f"Webhook secret starts with: {settings.STRIPE_WEBHOOK_SECRET[:10] if settings.STRIPE_WEBHOOK_SECRET else 'NOT SET'}")
    
    if not sig_header:
        print("ERROR: No signature header!")
        return HttpResponseBadRequest('No signature header')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        print(f"SUCCESS: Event type: {event['type']}")
    except ValueError as e:
        print(f"ERROR - ValueError: {e}")
        return HttpResponseBadRequest('Invalid payload')
    except stripe.error.SignatureVerificationError as e:
        print(f"ERROR - Signature verification failed: {e}")
        return HttpResponseBadRequest('Invalid signature')
    except Exception as e:
        print(f"ERROR - Unexpected: {type(e).__name__}: {e}")
        return HttpResponseBadRequest('Webhook error')
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        print("Processing checkout.session.completed")
        session = event['data']['object']
        
        # Get order from metadata
        order_id = session['metadata'].get('order_id')
        print(f"Order ID from metadata: {order_id}")
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                print(f"Found order: {order.order_number}")
                
                # Update order status
                order.status = 'confirmed'  # Fixed: was 'completed'
                order.stripe_payment_intent = session.get('payment_intent')
                order.paid_at = timezone.now()  # Add this
                order.save()
                
                # Create tickets for the order
                create_tickets_for_order(order)
                print("Tickets created")
                
                # Send confirmation email
                send_order_confirmation_email(order)
                print("Confirmation email sent!")
                
                # Update event tickets sold
                for item in order.items.all():
                    Event.objects.filter(pk=item.event.pk).update(
                        tickets_sold=models.F('tickets_sold') + item.quantity
                    )
                print("Event tickets updated")
                    
            except Order.DoesNotExist:
                print(f"ERROR: Order with id {order_id} not found")
        else:
            print("ERROR: No order_id in session metadata")
    
    return HttpResponse(status=200)

def create_tickets_for_order(order):
    """Create tickets for a completed order"""
    for item in order.items.all():
        item.generate_tickets()

def download_single_ticket(request, ticket_id):
    """Download a single ticket PDF"""
    from .models import Ticket
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Security check - ensure user owns this ticket or is staff
    if request.user.is_authenticated:
        if ticket.order.email != request.user.email and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to download this ticket.")
    else:
        # For anonymous users, you might want to add session-based checking
        # or require authentication
        pass
    
    # Generate PDF
    pdf_buffer = generate_single_ticket_pdf(ticket)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket-{ticket.ticket_number}.pdf"'
    response.write(pdf_buffer.getvalue())
    
    return response
def download_tickets(request, order_number):
    """Download tickets as PDF"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Security check
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You do not have permission to download these tickets')
            return redirect('event_management:event_list')
    
    # Generate PDF
    pdf_buffer = generate_tickets_pdf(order)
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tickets_{order_number}.pdf"'
    
    return response

def generate_order_qr_code(order):
    """Generate QR code for order"""
    # Create QR code data - could be order details or a URL
    qr_data = f"ORDER:{order.order_number}|DATE:{order.created_at.strftime('%Y%m%d')}|AMOUNT:{order.total_amount}"
    
    # Alternatively, use a URL to view the order
    # qr_data = f"http://localhost:8000/booking/order/success/{order.order_number}/"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return img_base64


def test_stripe(request):
    """Test Stripe with minimal setup"""
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {'name': 'Test Product'},
                    'unit_amount': 2000,  # £20.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:8000/',
            cancel_url='http://localhost:8000/',
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

    @login_required
    def user_orders(request):
        """Display user's order history"""
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'orders': orders,
            'title': 'My Orders'
        }
        return render(request, 'booking/user_orders.html', context)
@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    
    context = {
        "orders": orders,
        "title": "My Orders"
    }
    return render(request, "booking/user_orders.html", context)

@login_required
def order_detail(request, order_number):
    """Display detailed view of a specific order"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        "order": order,
        "title": f"Order {order_number}"
    }
    return render(request, "booking/order_detail.html", context)
