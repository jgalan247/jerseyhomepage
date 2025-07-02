#!/bin/bash
# Script to investigate migration dependencies

echo "=== 1. Listing all migration files ==="
docker-compose exec web bash -c "
for app in event_management booking payments; do
    echo \"--- \$app migrations ---\"
    if [ -d \"\$app/migrations\" ]; then
        ls -la \$app/migrations/*.py 2>/dev/null || echo 'No migrations found'
    else
        echo 'No migrations directory'
    fi
    echo
done
"

echo "=== 2. Searching for the problematic dependency ==="
docker-compose exec web bash -c "
echo 'Searching for 0002_update_payment_models references...'
grep -r '0002_update_payment_models' . --include='*.py' 2>/dev/null | grep -v __pycache__ || echo 'No references found'
"

echo "=== 3. Checking Django migration table ==="
docker-compose exec web python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT app, name FROM django_migrations ORDER BY app, id')
    migrations = cursor.fetchall()
    print('Applied migrations in database:')
    for app, name in migrations:
        print(f'  {app}: {name}')
"

echo "=== 4. Finding migration dependencies ==="
docker-compose exec web bash -c "
for migration in \$(find . -path '*/migrations/*.py' -name '*.py' | grep -E '(event_management|booking|payments)' | grep -v __init__); do
    if grep -q 'dependencies' \"\$migration\" 2>/dev/null; then
        echo \"Dependencies in \$migration:\"
        grep -A 10 'dependencies' \"\$migration\" | grep -B 10 ']' | head -20
        echo '---'
    fi
done
"
