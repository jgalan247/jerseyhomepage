#!/bin/bash
# Methods to drop a database with active connections

# Method 1: Stop only the web container (RECOMMENDED)
echo "=== Method 1: Stop web container, keep db running ==="
docker-compose stop web
docker-compose exec db psql -U jersey_user -d postgres -c "DROP DATABASE jersey_roothp;"
docker-compose exec db psql -U jersey_user -d postgres -c "CREATE DATABASE jersey_roothp;"
docker-compose start web
docker-compose exec web python manage.py migrate

# Method 2: Force disconnect all connections first
echo -e "\n=== Method 2: Force disconnect all connections ==="
docker-compose exec db psql -U jersey_user -d postgres -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'jersey_roothp' AND pid <> pg_backend_pid();
"
# Then immediately drop
docker-compose exec db psql -U jersey_user -d postgres -c "DROP DATABASE jersey_roothp;"
docker-compose exec db psql -U jersey_user -d postgres -c "CREATE DATABASE jersey_roothp;"

# Method 3: Connect to postgres database and force drop
echo -e "\n=== Method 3: Force drop with CASCADE (PostgreSQL 13+) ==="
docker-compose exec db psql -U jersey_user -d postgres -c "DROP DATABASE jersey_roothp WITH (FORCE);"

# Method 4: All in one command
echo -e "\n=== Method 4: One-liner to kill connections and drop ==="
docker-compose exec db psql -U jersey_user -d postgres << EOF
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'jersey_roothp' AND pid <> pg_backend_pid();
DROP DATABASE jersey_roothp;
CREATE DATABASE jersey_roothp;
EOF
