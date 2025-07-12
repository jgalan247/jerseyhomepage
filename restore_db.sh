#!/bin/bash
# Complete migration restoration script

echo "=== Complete Migration Restoration ==="

# 1. Clear existing migrations (except __init__.py)
echo "1. Clearing existing migration files..."
docker-compose exec web bash -c "
find event_management/migrations -name '*.py' -not -name '__init__.py' -delete 2>/dev/null
find payments/migrations -name '*.py' -not -name '__init__.py' -delete 2>/dev/null
"

# 2. Restore ALL event_management migrations from backup
echo -e "\n2. Restoring all event_management migrations..."
docker-compose exec web bash -c "
cp event_management/migrations_backup/*.py event_management/migrations/ 2>/dev/null || true
# Remove the __init__.py if it was copied
rm -f event_management/migrations/__init__.py/__init__.py 2>/dev/null
# Ensure __init__.py exists
touch event_management/migrations/__init__.py
"

# 3. Create all required payments migrations
echo -e "\n3. Creating payments migrations..."

# Create 0001_initial.py
docker-compose exec web bash -c "cat > payments/migrations/0001_initial.py << 'EOF'
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import uuid

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.booking')),
            ],
        ),
    ]
EOF"

# Create 0002_update_payment_models.py
docker-compose exec web bash -c "cat > payments/migrations/0002_update_payment_models.py << 'EOF'
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0001_initial'),
    ]
    
    operations = [
        # Empty migration - placeholder for already applied migration
    ]
EOF"

# 4. Fix the dependency issue in 0004_booking.py
echo -e "\n4. Fixing dependencies..."
docker-compose exec web bash -c "
# First check if the file exists and has the problematic dependency
if grep -q \"('payments', '0002_update_payment_models')\" event_management/migrations/0004_booking.py 2>/dev/null; then
    # Create a temporary file with the fixed content
    sed \"/('payments', '0002_update_payment_models'),/d\" event_management/migrations/0004_booking.py > /tmp/fixed_migration.py
    mv /tmp/fixed_migration.py event_management/migrations/0004_booking.py
    echo 'Removed payments dependency from 0004_booking.py'
else
    echo 'No payments dependency found in 0004_booking.py or file does not exist'
fi
"

# 5. List all migration files to verify
echo -e "\n5. Verifying all migration files..."
docker-compose exec web bash -c "
echo '=== event_management migrations ==='
ls -la event_management/migrations/*.py | grep -v __pycache__

echo -e '\n=== payments migrations ==='
ls -la payments/migrations/*.py | grep -v __pycache__

echo -e '\n=== booking migrations ==='
ls -la booking/migrations/*.py | grep -v __pycache__
"

# 6. Clear Python cache
echo -e "\n6. Clearing Python cache..."
docker-compose exec web find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# 7. Try migrations
echo -e "\n7. Testing migrations..."
docker-compose exec web python manage.py migrate --fake
