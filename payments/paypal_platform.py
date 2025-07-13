# payments/paypal_platform.py - Complete implementation
import logging

import paypalrestsdk
from django.conf import settings

logger = logging.getLogger(__name__)


class PayPalPlatformService:
    def __init__(self):
        paypalrestsdk.configure(
            {
                "mode": settings.PAYPAL_MODE,
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET,
            }
        )

    def create_order(self, event, pricing_plan):
        """Create a PayPal order for an event listing plan."""
        try:
            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": f"{settings.SITE_URL}/payments/platform/success",
                        "cancel_url": f"{settings.SITE_URL}/payments/platform/cancel",
                    },
                    "transactions": [
                        {
                            "amount": {
                                "total": f"{pricing_plan.price_per_event:.2f}",
                                "currency": "GBP",
                            },
                            "description": f"Listing fee for {event.title}",
                        }
                    ],
                }
            )

            if payment.create():
                approval_url = next(
                    (link.href for link in payment.links if link.rel == "approval_url"),
                    None,
                )
                logger.info("Created PayPal order %s", payment.id)
                return {
                    "success": True,
                    "order_id": payment.id,
                    "approval_url": approval_url,
                }

            logger.error("PayPal order creation failed: %s", payment.error)
            return {"success": False, "error": payment.error}

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("PayPal order creation error")
            return {"success": False, "error": str(exc)}

    def capture_order(self, order_id):
        """Capture an approved PayPal order."""
        try:
            payment = paypalrestsdk.Payment.find(order_id)
            payer_id = payment.payer.payer_info.payer_id

            if payment.execute({"payer_id": payer_id}):
                sale = payment.transactions[0].related_resources[0].sale
                logger.info("Captured PayPal order %s", order_id)
                return {"success": True, "capture_id": sale.id}

            logger.error("PayPal order capture failed: %s", payment.error)
            return {"success": False, "error": payment.error}

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("PayPal order capture error")
            return {"success": False, "error": str(exc)}
