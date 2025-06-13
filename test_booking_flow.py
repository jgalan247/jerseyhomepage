# test_booking_flow.py
# Run this from Django shell: python manage.py shell < test_booking_flow.py

from django.contrib.auth import get_user_model
from event_management.models import Event
from booking.models import Cart, CartItem, Order
from decimal import Decimal
import json

User = get_user_model()

print("=== Testing Jersey Event Booking Platform - Milestone 4 ===\n")

# Check if test data exists
print("1. Checking test data...")
events = Event.objects.filter(is_active=True)
print(f"   - Found {events.count()} active events")

users = User.objects.all()
print(f"   - Found {users.count()} users")

if events.count() == 0:
    print("   ⚠️  No events found. Run: python manage.py populate_test_data")
    exit()

# Test cart functionality
print("\n2. Testing cart functionality...")
test_user = User.objects.filter(email='user1@example.com').first()
if not test_user:
    print("   - Creating test user...")
    test_user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

# Create a cart
from django.contrib.sessions.backends.db import SessionStore
session = SessionStore()
session.create()

cart = Cart.objects.create(session_key=session.session_key)
print(f"   - Created cart with session: {cart.session_key}")

# Add items to cart
test_events = events[:3]  # Get first 3 events
for event in test_events:
    if event.price > 0:  # Only add paid events to cart
        cart_item = CartItem.objects.create(
            cart=cart,
            event=event,
            quantity=2,
            price=event.price
        )
        print(f"   - Added to cart: {event.title} x2 @ £{event.price}")

# Calculate total
total = sum(item.subtotal for item in cart.items.all())
print(f"   - Cart total: £{total}")

# Test order creation
print("\n3. Testing order creation...")
if cart.items.exists():
    order = Order.objects.create(
        user=test_user,
        customer_name="Test User",
        customer_email="test@example.com",
        total_amount=total,
        payment_status='pending',
        stripe_payment_intent_id='pi_test_123456'
    )
    print(f"   - Created order: {order.order_number}")
    
    # Create order items
    for cart_item in cart.items.all():
        order.items.create(
            event=cart_item.event,
            quantity=cart_item.quantity,
            price=cart_item.price
        )
    print(f"   - Added {order.items.count()} items to order")

# Check email templates
print("\n4. Checking email templates...")
import os
from django.conf import settings

email_html = os.path.join(settings.BASE_DIR, 'templates', 'booking', 'emails', 'order_confirmation.html')
email_txt = os.path.join(settings.BASE_DIR, 'templates', 'booking', 'emails', 'order_confirmation.txt')

if os.path.exists(email_html):
    print("   ✅ HTML email template exists")
else:
    print("   ❌ HTML email template missing - create templates/booking/emails/order_confirmation.html")

if os.path.exists(email_txt):
    print("   ✅ Text email template exists")
else:
    print("   ❌ Text email template missing - create templates/booking/emails/order_confirmation.txt")

# Check Stripe configuration
print("\n5. Checking Stripe configuration...")
stripe_public = getattr(settings, 'STRIPE_PUBLIC_KEY', None)
stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
stripe_webhook = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

if stripe_public and stripe_public.startswith('pk_test_'):
    print("   ✅ Stripe public key configured")
else:
    print("   ❌ Stripe public key missing - add STRIPE_PUBLIC_KEY to .env")

if stripe_secret and stripe_secret.startswith('sk_test_'):
    print("   ✅ Stripe secret key configured")
else:
    print("   ❌ Stripe secret key missing - add STRIPE_SECRET_KEY to .env")

if stripe_webhook and stripe_webhook.startswith('whsec_'):
    print("   ✅ Stripe webhook secret configured")
else:
    print("   ❌ Stripe webhook secret missing - add STRIPE_WEBHOOK_SECRET to .env")

# Check required packages
print("\n6. Checking required packages...")
try:
    import reportlab
    print("   ✅ reportlab installed (PDF generation)")
except ImportError:
    print("   ❌ reportlab not installed - run: pip install reportlab")

try:
    import qrcode
    print("   ✅ qrcode installed (QR code generation)")
except ImportError:
    print("   ❌ qrcode not installed - run: pip install qrcode")

try:
    import PIL
    print("   ✅ Pillow installed (image processing)")
except ImportError:
    print("   ❌ Pillow not installed - run: pip install Pillow")

try:
    import stripe
    print("   ✅ stripe installed (payment processing)")
except ImportError:
    print("   ❌ stripe not installed - run: pip install stripe")

# Summary
print("\n=== SUMMARY ===")
print("To complete Milestone 4:")
print("1. Save email templates to templates/booking/emails/")
print("2. Add Stripe keys to .env file")
print("3. Run: pip install reportlab qrcode pillow stripe")
print("4. Test the booking flow at http://localhost:8000")
print("\nTest accounts:")
print("- Admin: admin@jersey.live / admin123")
print("- User: user1@example.com / user123")

# Clean up test data
if order:
    print(f"\nCleaning up test order {order.order_number}...")
    order.delete()
if cart:
    cart.delete()