# event_management/pricing.py
# Replace your ENTIRE pricing.py file with this:

import os
from decimal import Decimal
from typing import Tuple

class PricingService:
    """Service for calculating event listing fees based on percentage model"""
    
    @staticmethod
    def get_pricing_tiers():
        """Get pricing tiers from environment variables"""
        return [
            {
                'name': os.getenv('TIER_1_NAME', 'Community'),
                'max_capacity': int(os.getenv('TIER_1_MAX_CAPACITY', '50')),
                'percentage': Decimal(os.getenv('TIER_1_PERCENTAGE', '4.0'))
            },
            {
                'name': os.getenv('TIER_2_NAME', 'Small'),
                'max_capacity': int(os.getenv('TIER_2_MAX_CAPACITY', '200')),
                'percentage': Decimal(os.getenv('TIER_2_PERCENTAGE', '3.5'))
            },
            {
                'name': os.getenv('TIER_3_NAME', 'Medium'),
                'max_capacity': int(os.getenv('TIER_3_MAX_CAPACITY', '500')),
                'percentage': Decimal(os.getenv('TIER_3_PERCENTAGE', '3.0'))
            },
            {
                'name': os.getenv('TIER_4_NAME', 'Large'),
                'max_capacity': int(os.getenv('TIER_4_MAX_CAPACITY', '999999')),
                'percentage': Decimal(os.getenv('TIER_4_PERCENTAGE', '2.5'))
            }
        ]
    
    @staticmethod
    def calculate_event_fee(capacity, is_free_event=False, ticket_price=None):
        """
        Calculate the listing fee for an event based on capacity and ticket price
        
        Args:
            capacity: Event capacity (int)
            is_free_event: Boolean indicating if event is free
            ticket_price: Price per ticket (Decimal) - if provided, uses percentage-based pricing
            
        Returns:
            Tuple of (fee_amount, tier_name)
        """
        # Get the appropriate tier based on capacity
        tiers = PricingService.get_pricing_tiers()
        tier = None
        
        for t in tiers:
            if capacity <= t['max_capacity']:
                tier = t
                break
        
        # Default to largest tier if capacity exceeds all tiers
        if tier is None:
            tier = tiers[-1]
        
        # If ticket_price is provided, use percentage-based calculation
        if ticket_price is not None:
            ticket_price = Decimal(str(ticket_price)) if ticket_price else Decimal('0')
            
            # Free events pay no fee
            if ticket_price <= 0 or is_free_event:
                return Decimal('0.00'), 'Free Event'
            
            # Calculate percentage-based fee
            percentage = tier['percentage'] / 100
            total_revenue = ticket_price * Decimal(capacity)
            fee = total_revenue * percentage
            
            # Apply minimum fee for paid events
            minimum_fee = Decimal(os.getenv('MINIMUM_PAID_EVENT_FEE', '15'))
            if fee < minimum_fee:
                fee = minimum_fee
            
            return fee.quantize(Decimal('0.01')), tier['name']
        
        # Legacy behavior when ticket_price is not provided (backward compatibility)
        if is_free_event:
            return Decimal('0.00'), 'Free Event'
        
        # Old fixed-fee behavior based on capacity tiers
        tier_fees = {
            'Community': Decimal('20.00'),
            'Small': Decimal('40.00'), 
            'Medium': Decimal('75.00'),
            'Large': Decimal('100.00')
        }
        return tier_fees.get(tier['name'], Decimal('20.00')), tier['name']
    
    @staticmethod
    def get_tier_for_capacity(capacity):
        """Get the pricing tier for a given capacity"""
        tiers = PricingService.get_pricing_tiers()
        
        for tier in tiers:
            if capacity <= tier['max_capacity']:
                return tier
        
        # Return the largest tier if capacity exceeds all tiers
        return tiers[-1]