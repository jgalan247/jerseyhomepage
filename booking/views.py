from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json
import qrcode
from io import BytesIO
import base64
import logging

from event_management.models import Event, TicketType
from .models import Cart, CartItem, Order, OrderItem, Ticket
from .utils import send_order_confirmation_email, generate_tickets_pdf, generate_single_ticket_pdf

logger = logging.getLogger(__name__)


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
    """Add ticket type to cart via AJAX - FIXED for TicketType"""
    try:
        event_id = request.POST.get('event_id')
        ticket_type_id = request.POST.get('ticket_type_id')  # ✅ REQUIRED: Get ticket type
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        
        if not ticket_type_id:
            return JsonResponse({'success': False, 'error': 'Ticket type is required'})
        
        event = get_object_or_404(Event, id=event_id, is_active=True)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)
        cart = get_or_create_cart(request)
        
        # ✅ FIXED: Check if this specific ticket type already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            ticket_type=ticket_type,  # Use ticket_type instead of event
            defaults={'quantity': 0, 'event': event}
        )
        
        # Check availability
        if cart_item.quantity + quantity > ticket_type.quantity_available:
            return JsonResponse({
                'success': False, 
                'error': f'Only {ticket_type.quantity_available - cart_item.quantity} tickets available'
            })
        
        # Update quantity
        cart_item.quantity += quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{ticket_type.name} added to cart',
            'cart_count': cart.total_items,
            'cart_total': str(cart.total_price)
        })
        
    except Exception as e:
        logger.error(f"Add to cart error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
    

@require_POST
def quick_add_to_cart(request):
    """HTMX endpoint for adding items to cart - FIXED for TicketType"""
    event_id = request.POST.get('event_id')
    ticket_type_id = request.POST.get('ticket_type_id', 1)  # Default to first ticket type
    
    event = get_object_or_404(Event, id=event_id)
    ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)
    cart = get_or_create_cart(request)
    
    # ✅ FIXED: Create or update cart item with ticket_type
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        ticket_type=ticket_type,  # Use ticket_type instead of event
        defaults={'quantity': 0, 'event': event}
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
                hx-vals='{{"event_id": "{event_id}", "ticket_type_id": "{ticket_type_id}"}}'
                class="btn btn-success">
            <i class="fas fa-check"></i> Added - Add Another
        </button>
    ''')
    
    return response


def cart_view(request):
    """Display cart page - FIXED to include ticket_type"""
    cart = get_or_create_cart(request)
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('event', 'ticket_type').all()  # ✅ Added ticket_type
    }
    return render(request, 'booking/cart.html', context)


@require_POST
def update_cart(request):
    """Update cart item quantity via AJAX - FIXED for TicketType"""
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity'))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity > 0:
            # ✅ FIXED: Check available tickets using ticket_type
            available = cart_item.ticket_type.quantity_available
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
        logger.error(f"Update cart error: {str(e)}")
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
        logger.error(f"Remove from cart error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def checkout_view(request):
    """Display checkout page with PayPal - FIXED for TicketType"""
    cart = get_or_create_cart(request)
    
    if cart.total_items == 0:
        messages.warning(request, 'Your cart is empty')
        return redirect('event_management:event_list')
    
    # ✅ FIXED: Build cart items using actual ticket types
    cart_items = []
    total = Decimal('0.00')
    
    for item in cart.items.select_related('event', 'ticket_type').all():
        # Format for your checkout template using actual ticket type data
        cart_items.append({
            'event': {
                'title': item.event.title,
                'start_date': item.event.date,  # Check if your Event model uses 'date' or 'start_date'
                'location': item.event.venue,
            },
            'ticket_type': {
                'name': item.ticket_type.name,  # ✅ FIXED: Use actual ticket type name
                'price': item.ticket_type.price  # ✅ FIXED: Use actual ticket type price
            },
            'quantity': item.quantity,
            'subtotal': item.subtotal  # This already uses ticket_type.price * quantity
        })
        total += item.subtotal
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', 'demo-client-id'),
    }
    
    # Pre-fill form if user is authenticated
    if request.user.is_authenticated:
        context['initial_data'] = {
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': getattr(request.user, 'phone_number', '')
        }
    else:
        context['initial_data'] = {}
    
    return render(request, 'booking/checkout.html', context)


@require_POST
@csrf_exempt
def create_ticket_order(request):
    """Create PayPal order for ticket purchase"""
    try:
        data = json.loads(request.body)
        cart = get_or_create_cart(request)
        
        if cart.total_items == 0:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Validate customer data
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field.replace("_", " ").title()} is required'}, status=400)
        
        # Calculate total from database cart
        total = cart.total_price
        
        # Store customer data in session for later use
        request.session['checkout_data'] = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'create_account': data.get('create_account', False)
        }
        
        # TODO: Create real PayPal order here using paypalrestsdk
        # For now, return mock order
        user_id = request.user.id if request.user.is_authenticated else 'guest'
        mock_order_id = f'TICKETS-{user_id}-{timezone.now().timestamp()}'
        
        logger.info(f"Creating ticket order: {mock_order_id}, total: £{total}, customer: {data.get('email')}")
        
        return JsonResponse({
            'id': mock_order_id,
            'amount': str(total)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Create ticket order error: {str(e)}")
        return JsonResponse({'error': 'Order creation failed'}, status=500)


@require_POST
@csrf_exempt
def capture_ticket_payment(request):
    """Capture PayPal payment for tickets - FIXED for TicketType"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        if not order_id:
            return JsonResponse({'error': 'Order ID is required'}, status=400)
        
        # Get checkout data from session
        checkout_data = request.session.get('checkout_data', {})
        cart = get_or_create_cart(request)
        
        if not checkout_data:
            return JsonResponse({'error': 'Session expired. Please try again.'}, status=400)
        
        if cart.total_items == 0:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # TODO: Verify payment with PayPal API
        # For now, just create the order
        
        # Create booking order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=checkout_data.get('email'),
                first_name=checkout_data.get('first_name'),
                last_name=checkout_data.get('last_name'),
                phone=checkout_data.get('phone', ''),
                paypal_order_id=order_id,
                status='confirmed',
                paid_at=timezone.now(),
                total_amount=cart.total_price
            )
            
            # ✅ FIXED: Create order items from cart with ticket_type
            for cart_item in cart.items.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    event=cart_item.event,
                    ticket_type=cart_item.ticket_type,  # ✅ FIXED: Include ticket_type
                    quantity=cart_item.quantity,
                    price=cart_item.ticket_type.price  # ✅ FIXED: Use ticket_type price
                )
                # Generate tickets using the model method
                order_item.generate_tickets()
            
            # Clear cart
            cart.items.all().delete()
            
            # Clear session data
            if 'checkout_data' in request.session:
                del request.session['checkout_data']
            
            # Send confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                logger.error(f"Email error: {e}")
        
        logger.info(f"Ticket payment captured: {order_id}, order: {order.order_number}")
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('booking:order_success', kwargs={'order_id': order.id})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Capture payment error: {str(e)}")
        return JsonResponse({'error': 'Payment processing failed'}, status=500)


def order_success(request, order_id):
    """Display order success page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You do not have permission to view this order')
            return redirect('event_management:event_list')
    
    context = {'order': order}
    return render(request, 'booking/order_success.html', context)


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


def download_single_ticket(request, ticket_id):
    """Download a single ticket PDF"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Security check
    if request.user.is_authenticated:
        if ticket.order.email != request.user.email and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to download this ticket.")
    
    # Generate PDF
    pdf_buffer = generate_single_ticket_pdf(ticket)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket-{ticket.ticket_number}.pdf"'
    response.write(pdf_buffer.getvalue())
    
    return response


@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'title': 'My Orders'
    }
    return render(request, 'booking/order_history.html', context)


# Keep this as an alias for backward compatibility
checkout = checkout_view