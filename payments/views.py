# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import logging

from .models import Order, OrderItem, PaymentAttempt, PaymentType, PaymentStatus
try:
    from .paypal_client import PayPalClient, format_amount
except ImportError:
    # Fallback to alternative implementation  
    from .paypal_client_alternative import PayPalClient, format_amount
from event_management.models import Event, TicketType, Booking

logger = logging.getLogger(__name__)

class TicketPurchaseView(View):
    """Handle ticket purchase flow"""
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        ticket_types = event.ticket_types.filter(is_active=True)
        
        context = {
            'event': event,
            'ticket_types': ticket_types,
        }
        return render(request, 'payments/ticket_purchase.html', context)
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Process form data
        selected_tickets = []
        total_amount = Decimal('0.00')
        
        for ticket_type in event.ticket_types.filter(is_active=True):
            quantity_key = f'quantity_{ticket_type.id}'
            quantity = int(request.POST.get(quantity_key, 0))
            
            if quantity > 0:
                if quantity > ticket_type.available_quantity:
                    messages.error(request, f'Only {ticket_type.available_quantity} {ticket_type.name} tickets available')
                    return redirect('payments:ticket_purchase', event_id=event.id)
                
                selected_tickets.append({
                    'ticket_type': ticket_type,
                    'quantity': quantity,
                    'total': ticket_type.price * quantity
                })
                total_amount += ticket_type.price * quantity
        
        if not selected_tickets:
            messages.error(request, 'Please select at least one ticket')
            return redirect('payments:ticket_purchase', event_id=event.id)
        
        # Create order
        order = Order.objects.create(
            event=event,
            user=request.user if request.user.is_authenticated else None,
            email=request.POST.get('email'),
            payment_type=PaymentType.TICKET_PURCHASE,
            total_amount=total_amount,
            description=f'Tickets for {event.title}'
        )
        
        # Create order items
        for ticket_data in selected_tickets:
            OrderItem.objects.create(
                order=order,
                ticket_type=ticket_data['ticket_type'],
                quantity=ticket_data['quantity'],
                price=ticket_data['ticket_type'].price,
                description=f"{ticket_data['ticket_type'].name} ticket"
            )
        
        # Create PayPal order
        return self._create_paypal_order(request, order)
    
    def _create_paypal_order(self, request, order):
        paypal_client = PayPalClient()
        
        order_data = {
            'amount': format_amount(order.total_amount),
            'currency': order.currency,
            'description': order.description,
            'return_url': request.build_absolute_uri(
                reverse('payments:payment_success', kwargs={'order_id': order.id})
            ),
            'cancel_url': request.build_absolute_uri(
                reverse('payments:payment_cancel', kwargs={'order_id': order.id})
            )
        }
        
        result = paypal_client.create_order(order_data)
        
        if result['success']:
            order.paypal_order_id = result['order_id']
            order.save()
            
            # Log attempt
            PaymentAttempt.objects.create(
                order=order,
                paypal_order_id=result['order_id'],
                status='created'
            )
            
            return redirect(result['approval_url'])
        else:
            # Log failed attempt
            PaymentAttempt.objects.create(
                order=order,
                status='failed',
                error_message=result['error']
            )
            
            messages.error(request, 'Payment initialization failed. Please try again.')
            return redirect('payments:ticket_purchase', event_id=order.event.id)

@method_decorator(login_required, name='dispatch')
class ListingFeeView(View):
    """Handle listing fee payment for event organizers"""
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        # Define listing fee tiers
        listing_options = [
            {'days': 30, 'price': Decimal('29.99'), 'popular': False},
            {'days': 60, 'price': Decimal('49.99'), 'popular': True},
            {'days': 90, 'price': Decimal('69.99'), 'popular': False},
        ]
        
        context = {
            'event': event,
            'listing_options': listing_options,
        }
        return render(request, 'payments/listing_fee.html', context)
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        # Get selected listing duration
        duration_days = int(request.POST.get('duration_days'))
        
        # Define pricing
        pricing = {30: 29.99, 60: 49.99, 90: 69.99}
        
        if duration_days not in pricing:
            messages.error(request, 'Invalid listing duration selected')
            return redirect('payments:listing_fee', event_id=event.id)
        
        amount = Decimal(str(pricing[duration_days]))
        
        # Create order
        order = Order.objects.create(
            event=event,
            user=request.user,
            email=request.user.email,
            payment_type=PaymentType.LISTING_FEE,
            total_amount=amount,
            description=f'Listing fee for {event.title} ({duration_days} days)',
            listing_duration_days=duration_days
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            quantity=1,
            price=amount,
            description=f'{duration_days}-day listing promotion'
        )
        
        # Create PayPal order
        return self._create_paypal_order(request, order)
    
    def _create_paypal_order(self, request, order):
        paypal_client = PayPalClient()
        
        order_data = {
            'amount': format_amount(order.total_amount),
            'currency': order.currency,
            'description': order.description,
            'return_url': request.build_absolute_uri(
                reverse('payments:payment_success', kwargs={'order_id': order.id})
            ),
            'cancel_url': request.build_absolute_uri(
                reverse('payments:payment_cancel', kwargs={'order_id': order.id})
            )
        }
        
        result = paypal_client.create_order(order_data)
        
        if result['success']:
            order.paypal_order_id = result['order_id']
            order.save()
            
            PaymentAttempt.objects.create(
                order=order,
                paypal_order_id=result['order_id'],
                status='created'
            )
            
            return redirect(result['approval_url'])
        else:
            PaymentAttempt.objects.create(
                order=order,
                status='failed',
                error_message=result['error']
            )
            
            messages.error(request, 'Payment initialization failed. Please try again.')
            return redirect('payments:listing_fee', event_id=order.event.id)

class PaymentSuccessView(View):
    """Handle successful payment return from PayPal"""
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        paypal_order_id = request.GET.get('token')
        
        if not paypal_order_id or paypal_order_id != order.paypal_order_id:
            messages.error(request, 'Invalid payment session')
            return redirect('events:event_detail', event_id=order.event.id)
        
        # Capture the payment
        paypal_client = PayPalClient()
        result = paypal_client.capture_order(paypal_order_id)
        
        if result['success']:
            # Update order
            order.status = PaymentStatus.COMPLETED
            order.paypal_capture_id = result['capture_id']
            order.save()
            
            # Process based on payment type
            if order.is_ticket_purchase:
                self._process_ticket_purchase(order)
            elif order.is_listing_fee:
                self._process_listing_fee(order)
            
            PaymentAttempt.objects.create(
                order=order,
                paypal_order_id=paypal_order_id,
                status='captured'
            )
            
            messages.success(request, 'Payment completed successfully!')
            
        else:
            order.status = PaymentStatus.FAILED
            order.save()
            
            PaymentAttempt.objects.create(
                order=order,
                paypal_order_id=paypal_order_id,
                status='capture_failed',
                error_message=result['error']
            )
            
            messages.error(request, 'Payment capture failed. Please contact support.')
        
        context = {
            'order': order,
            'success': result['success']
        }
        return render(request, 'payments/payment_success.html', context)
    
    def _process_ticket_purchase(self, order):
        """Create bookings for ticket purchase"""
        for item in order.items.all():
            if item.ticket_type:
                # Create booking
                booking = Booking.objects.create(
                    event=order.event,
                    user=order.user,
                    ticket_type=item.ticket_type,
                    quantity=item.quantity,
                    order=order,
                    total_amount=item.total_price,
                    attendee_name=order.user.get_full_name() if order.user else 'Guest',
                    attendee_email=order.email,
                    status='confirmed'
                )
                
                # Update ticket availability
                item.ticket_type.sold_quantity += item.quantity
                item.ticket_type.save()
    
    def _process_listing_fee(self, order):
        """Process listing fee payment"""
        # Update event listing status
        event = order.event
        event.is_promoted = True
        event.promotion_expires_at = timezone.now() + timedelta(days=order.listing_duration_days)
        event.save()

class PaymentCancelView(View):
    """Handle cancelled payments"""
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.status = PaymentStatus.CANCELLED
        order.save()
        
        PaymentAttempt.objects.create(
            order=order,
            status='cancelled'
        )
        
        messages.info(request, 'Payment was cancelled')
        
        context = {'order': order}
        return render(request, 'payments/payment_cancel.html', context)