from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from payments.paypal_platform import PayPalPlatformService


class PayPalPlatformServiceTests(TestCase):
    """Tests for PayPalPlatformService order creation and capture."""

    @patch("payments.paypal_platform.paypalrestsdk.Payment")
    def test_create_order_success(self, MockPayment):
        instance = MockPayment.return_value
        instance.create.return_value = True
        instance.id = "PAYID-1"
        instance.links = [
            SimpleNamespace(rel="approval_url", href="http://example.com/approve")
        ]

        service = PayPalPlatformService()
        event = SimpleNamespace(title="Test Event")
        plan = SimpleNamespace(price_per_event=Decimal("10.00"))

        result = service.create_order(event, plan)

        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "PAYID-1")
        self.assertEqual(result["approval_url"], "http://example.com/approve")
        instance.create.assert_called_once()

    @patch("payments.paypal_platform.paypalrestsdk.Payment")
    def test_create_order_failure(self, MockPayment):
        instance = MockPayment.return_value
        instance.create.return_value = False
        instance.error = {"message": "fail"}

        service = PayPalPlatformService()
        event = SimpleNamespace(title="Test Event")
        plan = SimpleNamespace(price_per_event=Decimal("10.00"))

        result = service.create_order(event, plan)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        instance.create.assert_called_once()

    @patch("payments.paypal_platform.paypalrestsdk.Payment")
    def test_capture_order_success(self, MockPayment):
        mock_payment = MockPayment.find.return_value
        mock_payment.payer = SimpleNamespace(
            payer_info=SimpleNamespace(payer_id="PAYER1")
        )
        mock_payment.execute.return_value = True
        mock_sale = MagicMock(id="SALE1")
        mock_related = MagicMock(sale=mock_sale)
        mock_payment.transactions = [MagicMock(related_resources=[mock_related])]

        service = PayPalPlatformService()
        result = service.capture_order("ORDER1")

        self.assertTrue(result["success"])
        self.assertEqual(result["capture_id"], "SALE1")
        mock_payment.execute.assert_called_once_with({"payer_id": "PAYER1"})
        MockPayment.find.assert_called_once_with("ORDER1")

    @patch("payments.paypal_platform.paypalrestsdk.Payment")
    def test_capture_order_failure(self, MockPayment):
        mock_payment = MockPayment.find.return_value
        mock_payment.payer = SimpleNamespace(
            payer_info=SimpleNamespace(payer_id="PAYER1")
        )
        mock_payment.execute.return_value = False
        mock_payment.error = {"message": "error"}

        service = PayPalPlatformService()
        result = service.capture_order("ORDER1")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        mock_payment.execute.assert_called_once_with({"payer_id": "PAYER1"})
        MockPayment.find.assert_called_once_with("ORDER1")
