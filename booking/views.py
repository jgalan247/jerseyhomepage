# booking/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import stripe
import json

# Move imports inside functions to avoid circular import issues
from .models import Cart, CartItem, Order, OrderItem, Ticket

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_cart(request):
    """Get or create cart based on session"""
    if not request.session.session_key:
        request.session.create()
    
    cart, created = Cart.objects.get_or_create(
        session_key=request.session.session_key
    )
    return cart


def cart_context(request):
    """Context processor for cart data"""
    try:
        cart = get_or_create_cart(request)
        return {
            'cart': cart,
            'cart_items_count': cart.total_items,
            'cart_total': cart.total_price,
        }
    except Exception:
        # Return empty cart data if there's any error
        return {
            'cart': None,
            'cart_items_count': 0,
            'cart_total': 0,
        }


@require_POST
def add_to_cart(request, event_slug):
    """AJAX endpoint to add event to cart"""
    from event_management.models import Event
    try:
        event = get_object_or_404(Event, slug=event_slug)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        
        # Check if event has enough capacity
        if event.capacity and event.tickets_sold + quantity > event.capacity:
            available = event.capacity - event.tickets_sold
            return JsonResponse({
                'success': False, 
                'error': f'Only {available} tickets available'
            })
        
        cart = get_or_create_cart(request)
        
        # Check if item already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={
                'quantity': quantity,
                'price_at_time': event.price
            }
        )
        
        if not created:
            # Update quantity if already in cart
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{event.title} added to cart',
            'cart_items_count': cart.total_items,
            'cart_total': str(cart.total_price),
            'item_total': str(cart_item.total_price)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def cart_view(request):
    """Display cart page"""
    cart = get_or_create_cart(request)
    
    # Check for sold out events
    for item in cart.items.all():
        if item.event.is_sold_out:
            messages.warning(request, f'{item.event.title} is now sold out and has been removed from your cart')
            item.delete()
        elif item.event.capacity and item.event.tickets_sold + item.quantity > item.event.capacity:
            available = item.event.capacity - item.event.tickets_sold
            item.quantity = available
            item.save()
            messages.info(request, f'Quantity for {item.event.title} adjusted to {available} (maximum available)')
    
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('event', 'event__category').all()
    }
    return render(request, 'booking/cart.html', context)


@require_POST
def update_cart(request):
    """AJAX endpoint to update cart item quantity"""
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity < 1:
            cart_item.delete()
            message = f'{cart_item.event.title} removed from cart'
        else:
            # Check capacity
            event = cart_item.event
            if event.capacity and event.tickets_sold + quantity > event.capacity:
                available = event.capacity - event.tickets_sold
                return JsonResponse({
                    'success': False,
                    'error': f'Only {available} tickets available'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_items_count': cart.total_items,
            'cart_total': str(cart.total_price),
            'item_total': str(cart_item.total_price) if cart_item.id else '0'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    event_title = cart_item.event.title
    cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{event_title} removed from cart',
            'cart_items_count': cart.total_items,
            'cart_total': str(cart.total_price)
        })
    
    messages.success(request, f'{event_title} removed from cart')
    return redirect('booking:cart')


def checkout_view(request):
    """Display checkout page"""
    cart = get_or_create_cart(request)
    
    if cart.total_items == 0:
        messages.info(request, 'Your cart is empty')
        return redirect('event_management:event_list')
    
    # Final availability check
    for item in cart.items.all():
        if item.event.is_sold_out:
            messages.error(request, f'{item.event.title} is sold out')
            item.delete()
    
    if cart.total_items == 0:
        return redirect('event_management:event_list')
    
    # Pre-fill form if user is authenticated
    initial_data = {}
    if request.user.is_authenticated:
        initial_data = {
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
    
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('event').all(),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'initial_data': initial_data,
    }
    return render(request, 'booking/checkout.html', context)


@require_POST
def process_payment(request):
    """Process payment with Stripe"""
    cart = get_or_create_cart(request)
    
    if cart.total_items == 0:
        return JsonResponse({'success': False, 'error': 'Cart is empty'})
    
    try:
        # Get form data
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone', '')
        
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                total_amount=cart.total_price,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            
            # Create order items
            line_items = []
            for cart_item in cart.items.all():
                # Final availability check
                event = cart_item.event
                if event.capacity and event.tickets_sold + cart_item.quantity > event.capacity:
                    raise ValidationError(f'Not enough tickets available for {event.title}')
                
                OrderItem.objects.create(
                    order=order,
                    event=event,
                    quantity=cart_item.quantity,
                    price=cart_item.price_at_time
                )
                
                # Prepare Stripe line items
                line_items.append({
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': event.title,
                            'description': f'Ticket for {event.title} on {event.date}',
                            'images': [request.build_absolute_uri(event.image.url)] if event.image else [],
                        },
                        'unit_amount': int(cart_item.price_at_time * 100),  # Convert to pence
                    },
                    'quantity': cart_item.quantity,
                })
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                customer_email=email,
                success_url=request.build_absolute_uri(
                    reverse('booking:order_success', args=[order.order_number])
                ) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('booking:checkout')),
                metadata={
                    'order_number': order.order_number
                }
            )
            
            # Save Stripe session ID
            order.stripe_checkout_session = checkout_session.id
            order.save()
            
            return JsonResponse({
                'success': True,
                'checkout_url': checkout_session.url
            })
            
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except stripe.error.StripeError as e:
        return JsonResponse({'success': False, 'error': 'Payment processing error. Please try again.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def order_success(request, order_number):
    """Order success page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Verify session if provided
    session_id = request.GET.get('session_id')
    if session_id and order.stripe_checkout_session == session_id:
        # Clear cart
        cart = get_or_create_cart(request)
        cart.clear()
        
        # Send confirmation email (async task in production)
        if not order.is_paid:
            # This would typically be handled by webhook, but for redundancy
            order.mark_as_paid()
            send_order_confirmation_email(order)
    
    context = {
        'order': order,
        'order_items': order.items.select_related('event').all()
    }
    return render(request, 'booking/order_success.html', context)


@login_required
def order_history(request):
    """Display user's order history"""
    orders = request.user.orders.select_related().prefetch_related(
        'items__event', 'items__tickets'
    ).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'booking/order_history.html', context)


def order_detail(request, order_number):
    """Display order details"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check permission
    if not request.user.is_authenticated and order.email != request.session.get('guest_email'):
        if request.method == 'POST':
            email = request.POST.get('email')
            if email == order.email:
                request.session['guest_email'] = email
            else:
                messages.error(request, 'Invalid email for this order')
                return redirect('booking:order_lookup')
        else:
            return render(request, 'booking/order_verify_email.html', {'order_number': order_number})
    
    elif request.user.is_authenticated and order.user != request.user:
        messages.error(request, 'You do not have permission to view this order')
        return redirect('booking:order_history')
    
    context = {
        'order': order,
        'order_items': order.items.select_related('event').prefetch_related('tickets').all()
    }
    return render(request, 'booking/order_detail.html', context)


def download_tickets(request, order_number):
    """Download tickets as PDF"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check permission
    if request.user.is_authenticated:
        if order.user != request.user:
            messages.error(request, 'You do not have permission to download these tickets')
            return redirect('booking:order_history')
    else:
        if order.email != request.session.get('guest_email'):
            messages.error(request, 'Please verify your email first')
            return redirect('booking:order_detail', order_number=order_number)
    
    if not order.is_paid:
        messages.error(request, 'Order is not paid')
        return redirect('booking:order_detail', order_number=order_number)
    
    # Generate PDF
    pdf_response = generate_ticket_pdf(order)
    return pdf_response


@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_number = session['metadata']['order_number']
        
        try:
            order = Order.objects.get(order_number=order_number)
            order.stripe_payment_intent = session.get('payment_intent')
            order.mark_as_paid()
            
            # Send confirmation email
            send_order_confirmation_email(order)
            
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    
    return JsonResponse({'status': 'success'})