# payments/paypal_payments.py

import json
import uuid
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
import requests
import logging

logger = logging.getLogger(__name__)


class PayPalPaymentProcessor:
    """Handle PayPal Commerce Platform payments with marketplace fees"""
    
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = settings.PAYPAL_BASE_URL
        self.platform_fee_percentage = Decimal('0.05')  # 5% platform fee
        
    def get_access_token(self):
        """Get OAuth2 access token"""
        auth = (self.client_id, self.client_secret)
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        }
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            headers=headers,
            data=data,
            auth=auth
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        raise Exception(f"Failed to get access token: {response.text}")
    
    def create_order(self, event, tickets, organizer):
        """
        Create PayPal order with platform fee
        
        Args:
            event: Event model instance
            tickets: List of ticket types and quantities
            organizer: Organizer model instance
        """
        token = self.get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'PayPal-Partner-Attribution-Id': settings.PAYPAL_PARTNER_ID,
        }
        
        # Calculate totals
        subtotal = sum(
            Decimal(str(ticket['price'])) * ticket['quantity'] 
            for ticket in tickets
        )
        platform_fee = (subtotal * self.platform_fee_percentage).quantize(Decimal('0.01'))
        
        # Build order data
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": f"event_{event.id}",
                "description": f"Tickets for {event.title}",
                "amount": {
                    "currency_code": "GBP",
                    "value": str(subtotal),
                    "breakdown": {
                        "item_total": {
                            "currency_code": "GBP",
                            "value": str(subtotal)
                        }
                    }
                },
                "payee": {
                    "merchant_id": organizer.paypal_merchant_id
                },
                "payment_instruction": {
                    "disbursement_mode": "INSTANT",
                    "platform_fees": [{
                        "amount": {
                            "currency_code": "GBP",
                            "value": str(platform_fee)
                        }
                    }]
                },
                "items": [
                    {
                        "name": f"{ticket['name']} - {event.title}",
                        "quantity": str(ticket['quantity']),
                        "unit_amount": {
                            "currency_code": "GBP",
                            "value": str(ticket['price'])
                        }
                    } for ticket in tickets
                ]
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "brand_name": "Jersey Events Platform",
                        "locale": "en-GB",
                        "landing_page": "NO_PREFERENCE",
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "PAY_NOW",
                        "return_url": f"{settings.SITE_URL}/payments/success",
                        "cancel_url": f"{settings.SITE_URL}/events/{event.slug}"
                    }
                }
            }
        }
        
        response = requests.post(
            f"{self.base_url}/v2/checkout/orders",
            headers=headers,
            json=order_data
        )
        
        if response.status_code == 201:
            return response.json()
        raise Exception(f"Failed to create order: {response.text}")
    
    def capture_order(self, order_id):
        """Capture payment for completed order"""
        token = self.get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        
        response = requests.post(
            f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        raise Exception(f"Failed to capture order: {response.text}")
    
    def refund_payment(self, capture_id, amount=None, reason="Customer requested"):
        """Process refund for captured payment"""
        token = self.get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        
        data = {
            "note_to_payer": reason
        }
        
        if amount:
            data["amount"] = {
                "currency_code": "GBP",
                "value": str(amount)
            }
        
        response = requests.post(
            f"{self.base_url}/v2/payments/captures/{capture_id}/refund",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            return response.json()
        raise Exception(f"Failed to process refund: {response.text}")


# views.py - Example checkout view
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Event, Order, OrderItem


def checkout(request, event_slug):
    """Handle event ticket checkout"""
    event = get_object_or_404(Event, slug=event_slug)
    
    if request.method == 'POST':
        # Get ticket selections from form
        tickets = []
        for ticket_type in event.ticket_types.all():
            quantity = int(request.POST.get(f'ticket_{ticket_type.id}', 0))
            if quantity > 0:
                tickets.append({
                    'id': ticket_type.id,
                    'name': ticket_type.name,
                    'price': ticket_type.price,
                    'quantity': quantity
                })
        
        if not tickets:
            messages.error(request, "Please select at least one ticket")
            return redirect('event_detail', slug=event_slug)
        
        try:
            # Create PayPal order
            processor = PayPalPaymentProcessor()
            paypal_order = processor.create_order(event, tickets, event.organizer)
            
            # Create pending order in database
            order = Order.objects.create(
                event=event,
                user=request.user if request.user.is_authenticated else None,
                email=request.POST.get('email'),
                paypal_order_id=paypal_order['id'],
                status='pending',
                total_amount=sum(t['price'] * t['quantity'] for t in tickets)
            )
            
            # Add order items
            for ticket in tickets:
                OrderItem.objects.create(
                    order=order,
                    ticket_type_id=ticket['id'],
                    quantity=ticket['quantity'],
                    price=ticket['price']
                )
            
            # Return PayPal order ID for frontend
            return JsonResponse({
                'id': paypal_order['id'],
                'order_id': order.id
            })
            
        except Exception as e:
            logger.error(f"Checkout error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return render(request, 'checkout.html', {'event': event})


@csrf_exempt
def payment_complete(request):
    """Handle payment completion from PayPal"""
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('orderID')
        
        try:
            # Capture payment
            processor = PayPalPaymentProcessor()
            capture = processor.capture_order(order_id)
            
            # Update order status
            order = Order.objects.get(paypal_order_id=order_id)
            order.status = 'completed'
            order.paypal_capture_id = capture['purchase_units'][0]['payments']['captures'][0]['id']
            order.save()
            
            # Send confirmation email, generate tickets, etc.
            order.send_confirmation_email()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Payment completion error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

