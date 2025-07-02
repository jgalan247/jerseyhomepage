# payments/paypal_client.py
import os
from decimal import Decimal
from django.conf import settings
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersGetRequest, OrdersCaptureRequest
import logging

logger = logging.getLogger(__name__)

class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.mode = settings.PAYPAL_MODE
        
        # Choose environment
        if self.mode == 'sandbox':
            environment = SandboxEnvironment(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        else:
            environment = LiveEnvironment(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        
        self.client = PayPalHttpClient(environment)
    
    def create_order(self, order_data):
        """
        Create a PayPal order
        order_data should contain: amount, currency, description, return_url, cancel_url
        """
        try:
            request = OrdersCreateRequest()
            request.prefer('return=representation')
            
            request.request_body({
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": order_data.get('currency', 'USD'),
                        "value": str(order_data['amount'])
                    },
                    "description": order_data.get('description', 'Payment')
                }],
                "application_context": {
                    "brand_name": "Your Event Platform",
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": order_data['return_url'],
                    "cancel_url": order_data['cancel_url']
                }
            })
            
            response = self.client.execute(request)
            logger.info(f"PayPal order created: {response.result.id}")
            return {
                'success': True,
                'order_id': response.result.id,
                'approval_url': self._get_approval_url(response.result.links),
                'response': response.result
            }
            
        except Exception as e:
            logger.error(f"PayPal order creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_order(self, order_id):
        """Get order details from PayPal"""
        try:
            request = OrdersGetRequest(order_id)
            response = self.client.execute(request)
            
            return {
                'success': True,
                'order': response.result
            }
            
        except Exception as e:
            logger.error(f"Failed to get PayPal order {order_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def capture_order(self, order_id):
        """Capture an approved PayPal order"""
        try:
            request = OrdersCaptureRequest(order_id)
            response = self.client.execute(request)
            
            capture_result = response.result
            logger.info(f"PayPal order captured: {order_id}")
            
            return {
                'success': True,
                'capture_id': capture_result.purchase_units[0].payments.captures[0].id,
                'status': capture_result.status,
                'response': capture_result
            }
            
        except Exception as e:
            logger.error(f"PayPal order capture failed for {order_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_approval_url(self, links):
        """Extract approval URL from PayPal response links"""
        for link in links:
            if link.rel == "approve":
                return link.href
        return None

# Utility functions
def format_amount(amount):
    """Format amount for PayPal (2 decimal places)"""
    if isinstance(amount, Decimal):
        return "{:.2f}".format(amount)
    return "{:.2f}".format(float(amount))