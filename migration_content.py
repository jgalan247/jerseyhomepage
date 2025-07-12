# Save this as migration_content.py
migration_content = '''# Generated migration for adding listing and approval fields
from django.db import migrations, models
from decimal import Decimal
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_user_email_verification_token'),
        ('event_management', '0005_event_is_premium'),  # Update this to your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='listing_fee',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), help_text='Platform listing fee for this event', max_digits=10),
        ),
        migrations.AddField(
            model_name='event',
            name='listing_tier',
            field=models.CharField(blank=True, default='', help_text='Pricing tier applied', max_length=50),
        ),
        migrations.AddField(
            model_name='event',
            name='listing_paid',
            field=models.BooleanField(default=False, help_text='Has the listing fee been paid?'),
        ),
        migrations.AddField(
            model_name='event',
            name='listing_paid_at',
            field=models.DateTimeField(blank=True, help_text='When the listing fee was paid', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('pending_payment', 'Pending Payment'), ('pending_review', 'Pending Review'), ('approved', 'Approved'), ('published', 'Published'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='draft', help_text='Event status in the system', max_length=20),
        ),
        migrations.AddField(
            model_name='event',
            name='admin_notes',
            field=models.TextField(blank=True, default='', help_text='Notes from admin (rejection reasons, etc.)'),
        ),
        migrations.AddField(
            model_name='event',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, help_text='Admin who reviewed this event', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_events', to='authentication.user'),
        ),
        migrations.AddField(
            model_name='event',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, help_text='When the event was reviewed', null=True),
        ),
    ]
'''

# Write to the migration file
import os
migration_file = 'event_management/migrations/0006_add_listing_and_approval_fields.py'
with open(migration_file, 'w') as f:
    f.write(migration_content)
print(f"Migration written to {migration_file}")
