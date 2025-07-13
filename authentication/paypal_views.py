# authentication/paypal_views.py

import json
import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Organizer
import logging

logger = logging.getLogger(__name__)

class PayPalClient:
    """PayPal API client for Commerce Platform"""
    
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.partner_id = settings.PAYPAL_PARTNER_ID  # Your BN Code
        self.base_url = settings.PAYPAL_BASE_URL  # sandbox or live
        
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
    
    def create_partner_referral(self, organizer):
        """Create partner referral for organizer onboarding"""
        token = self.get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        
        # Build referral data
        data = {
            "email": organizer.business_email,
            "preferred_language_code": "en-GB",
            "tracking_id": str(organizer.id),  # Your internal tracking
            "partner_config_override": {
                "return_url": self.build_absolute_uri(
                    reverse('authentication:paypal_connect_return')
                ),
                "return_url_description": "Return to Jersey Events Platform",
                "action_renewal_url": self.build_absolute_uri(
                    reverse('authentication:paypal_connect_refresh')
                ),
                "show_add_credit_card": True
            },
            "operations": [
                {
                    "operation": "API_INTEGRATION",
                    "api_integration_preference": {
                        "rest_api_integration": {
                            "integration_method": "PAYPAL",
                            "integration_type": "THIRD_PARTY",
                            "third_party_details": {
                                "features": ["PAYMENT", "REFUND", "PARTNER_FEE"]
                            }
                        }
                    }
                }
            ],
            "products": ["EXPRESS_CHECKOUT"],
            "legal_consents": [
                {
                    "type": "SHARE_DATA_CONSENT",
                    "granted": True
                }
            ],
            "business_entity": {
                "business_type": "COMPANY",
                "names": [
                    {
                        "type": "LEGAL_NAME",
                        "name": organizer.company_name
                    }
                ],
                "emails": [
                    {
                        "type": "BUSINESS",
                        "email": organizer.business_email
                    }
                ],
                "phones": [
                    {
                        "type": "BUSINESS",
                        "country_code": "44",
                        "national_number": organizer.business_phone.replace('+44', '')
                    }
                ],
                "addresses": [
                    {
                        "type": "WORK",
                        "address_line_1": organizer.address_line_1,
                        "address_line_2": organizer.address_line_2,
                        "admin_area_2": organizer.city,
                        "admin_area_1": organizer.parish,
                        "postal_code": organizer.postal_code,
                        "country_code": "GB"
                    }
                ]
            }
        }
        
        response = requests.post(
            f"{self.base_url}/v2/customer/partner-referrals",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            return response.json()
        raise Exception(f"Failed to create referral: {response.text}")


@login_required
def paypal_connect_onboarding(request):
    """Start or continue PayPal Commerce Platform onboarding"""
    try:
        organizer = request.user.organizer
    except Organizer.DoesNotExist:
        messages.error(request, "You need to be an organizer to set up PayPal payments.")
        return redirect('home')
    
    if not organizer.is_verified:
        messages.warning(request, "Your organizer account must be verified before setting up payments.")
        return redirect('event_management:organizer_dashboard')
    
    try:
        client = PayPalClient()
        
        # Create partner referral
        referral = client.create_partner_referral(organizer)
        
        # Save the referral ID for tracking
        organizer.paypal_referral_id = referral['links'][0]['href'].split('/')[-1]
        organizer.save()
        
        # Find the action URL for redirect
        action_url = next(
            link['href'] for link in referral['links'] 
            if link['rel'] == 'action_url'
        )
        
        messages.info(request, "Redirecting to PayPal for account setup...")
        return redirect(action_url)
        
    except Exception as e:
        logger.error(f"PayPal onboarding error: {str(e)}")
        messages.error(request, "Error starting PayPal setup. Please try again.")
        return redirect('event_management:organizer_dashboard')


@login_required
def paypal_connect_return(request):
    """Handle return from PayPal onboarding"""
    try:
        organizer = request.user.organizer
    except Organizer.DoesNotExist:
        return redirect('home')
    
    # Get merchant ID from query params
    merchant_id = request.GET.get('merchantIdInPayPal')
    permissions_granted = request.GET.get('permissionsGranted')
    consent_status = request.GET.get('consentStatus')
    
    if merchant_id:
        organizer.paypal_merchant_id = merchant_id
        organizer.paypal_onboarding_complete = (
            permissions_granted == 'true' and 
            consent_status == 'true'
        )
        organizer.paypal_last_update = timezone.now()
        organizer.save()
        
        if organizer.paypal_onboarding_complete:
            messages.success(
                request,
                "Excellent! Your PayPal account is connected. You can now receive payments for your events."
            )
            # Fetch additional merchant info if needed
            _fetch_merchant_status(organizer)
        else:
            messages.warning(
                request,
                "PayPal setup incomplete. Please complete all required steps."
            )
    else:
        messages.error(request, "PayPal setup was not completed.")
    
    return redirect('event_management:organizer_dashboard')


@login_required
def paypal_connect_refresh(request):
    """Handle refresh/continuation of PayPal onboarding"""
    messages.info(request, "Please continue your PayPal setup.")
    return redirect('authentication:paypal_connect_onboarding')


@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request):
    """Handle PayPal webhooks for account updates"""
    # Verify webhook signature
    if not _verify_webhook_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    try:
        event = json.loads(request.body)
        event_type = event.get('event_type')
        
        # Handle different webhook events
        if event_type == 'MERCHANT.ONBOARDING.COMPLETED':
            merchant_id = event['resource']['merchant_id']
            try:
                organizer = Organizer.objects.get(paypal_merchant_id=merchant_id)
                organizer.paypal_onboarding_complete = True
                organizer.paypal_payments_receivable = True
                organizer.paypal_last_update = timezone.now()
                organizer.save()
                logger.info(f"Onboarding completed for {organizer.company_name}")
            except Organizer.DoesNotExist:
                logger.error(f"No organizer found for merchant {merchant_id}")
                
        elif event_type == 'MERCHANT.PARTNER-CONSENT.REVOKED':
            merchant_id = event['resource']['merchant_id']
            try:
                organizer = Organizer.objects.get(paypal_merchant_id=merchant_id)
                organizer.paypal_onboarding_complete = False
                organizer.paypal_payments_receivable = False
                organizer.save()
                logger.info(f"Consent revoked for {organizer.company_name}")
            except Organizer.DoesNotExist:
                logger.error(f"No organizer found for merchant {merchant_id}")
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({'error': 'Processing failed'}, status=500)
    
    return JsonResponse({'status': 'success'})


def _verify_webhook_signature(request):
    """Verify PayPal webhook signature"""
    if getattr(settings, 'SKIP_WEBHOOK_VERIFICATION', False):
        logger.warning("Skipping PayPal webhook signature verification")
        return True

    required_headers = [
        'HTTP_PAYPAL_TRANSMISSION_ID',
        'HTTP_PAYPAL_TRANSMISSION_TIME',
        'HTTP_PAYPAL_CERT_URL',
        'HTTP_PAYPAL_AUTH_ALGO',
        'HTTP_PAYPAL_TRANSMISSION_SIG',
    ]

    if not all(h in request.META for h in required_headers):
        logger.error("Missing PayPal webhook headers")
        return False

    client = PayPalClient()
    try:
        token = client.get_access_token()
    except Exception as e:
        logger.error(f"Failed to obtain PayPal token: {e}")
        return False

    payload = {
        "transmission_id": request.META['HTTP_PAYPAL_TRANSMISSION_ID'],
        "transmission_time": request.META['HTTP_PAYPAL_TRANSMISSION_TIME'],
        "cert_url": request.META['HTTP_PAYPAL_CERT_URL'],
        "auth_algo": request.META['HTTP_PAYPAL_AUTH_ALGO'],
        "transmission_sig": request.META['HTTP_PAYPAL_TRANSMISSION_SIG'],
        "webhook_id": settings.PAYPAL_WEBHOOK_ID,
        "webhook_event": json.loads(request.body.decode('utf-8') or '{}'),
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    response = requests.post(
        f"{client.base_url}/v1/notifications/verify-webhook-signature",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        verification_status = response.json().get('verification_status')
        return verification_status == 'SUCCESS'

    logger.error(
        f"Webhook verification API failed: {response.status_code} {response.text}"
    )
    return False


def _fetch_merchant_status(organizer):
    """Fetch detailed merchant status from PayPal"""
    client = PayPalClient()
    token = client.get_access_token()
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # Get merchant status
    response = requests.get(
        f"{client.base_url}/v1/customer/partners/{client.partner_id}/merchant-integrations/{organizer.paypal_merchant_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        # Update organizer with capabilities
        organizer.paypal_payments_receivable = data.get('payments_receivable', False)
        organizer.paypal_primary_email = data.get('primary_email', '')
        organizer.save()


