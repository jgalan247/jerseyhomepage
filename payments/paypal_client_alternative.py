import requests
import base64
import json
from decimal import Decimal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.mode = settings.PAYPAL_MODE
        
        if self.mode == "sandbox":
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
        
        self.access_token = None
    
    def get_access_token(self):
        return "dummy_token"
    
    def create_order(self, order_data):
        return {
            "success": False,
            "error": "PayPal not configured"
        }
    
    def capture_order(self, order_id):
        return {
            "success": False,
            "error": "PayPal not configured"
        }

def format_amount(amount):
    if isinstance(amount, Decimal):
        return "{:.2f}".format(amount)
    return "{:.2f}".format(float(amount))
