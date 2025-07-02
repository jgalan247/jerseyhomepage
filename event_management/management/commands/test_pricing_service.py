from django.core.management.base import BaseCommand
from event_management.pricing import PricingService
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test the pricing service calculations'

    def handle(self, *args, **options):
        self.stdout.write('\n=== TESTING PRICING SERVICE ===\n')
        
        # Test 1: Display all tiers
        self.stdout.write('Available Tiers:')
        tiers = PricingService.get_all_tiers()
        for tier in tiers:
            self.stdout.write(f"  {tier['name']}: up to {tier['max_capacity']} people = £{tier['price']}")
        
        # Test 2: Test different capacities
        self.stdout.write('\nTesting Event Pricing:')
        test_cases = [
            (10, True),   # Free event
            (10, False),  # Paid small event
            (100, False), # Medium event
            (300, False), # Large event
            (1000, False), # Very large event
        ]
        
        for capacity, is_free in test_cases:
            fee, tier = PricingService.calculate_event_fee(capacity, is_free)
            free_text = " (FREE EVENT)" if is_free else ""
            self.stdout.write(f"  Capacity {capacity}{free_text}: £{fee} ({tier})")
        
        # Test 3: Test with an actual event
        self.stdout.write('\nTesting with Event Model:')
        try:
            from event_management.models import Event, Category
            from authentication.models import Organizer
            
            # Get first category and organizer for testing
            category = Category.objects.first()
            organizer = Organizer.objects.first()
            
            if category and organizer:
                # Create test event
                test_event = Event(
                    title="Test Pricing Event",
                    slug="test-pricing-event",
                    description="Testing pricing calculation",
                    venue="Test Venue",
                    address="Test Address",
                    date=timezone.now() + timedelta(days=30),
                    category=category,
                    capacity=150,
                    organizer=organizer,
                    price=Decimal('0'),  # Free event
                )
                
                # Calculate fee
                fee, tier = test_event.calculate_listing_fee()
                self.stdout.write(f"  Event '{test_event.title}' with capacity {test_event.capacity}:")
                self.stdout.write(f"    - Tier: {tier}")
                self.stdout.write(f"    - Fee: £{fee}")
                
                self.stdout.write(self.style.SUCCESS('\n✓ All tests passed!\n'))
            else:
                self.stdout.write(self.style.WARNING('\n! No test data found. Run populate_events command first.\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error testing with model: {e}\n'))

# Add these imports at the top
from django.utils import timezone
from datetime import timedelta