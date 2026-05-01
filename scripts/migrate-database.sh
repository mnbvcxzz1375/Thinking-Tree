#!/bin/bash
# Database migration script

set -e

# Default database URL
DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/thinking_tree"}

echo "🔄 Running database migrations..."
echo "Database URL: $DATABASE_URL"

# Check if we're in the right directory
if [ ! -f "backend/migrations/alembic.ini" ]; then
    echo "❌ Alembic configuration not found. Please run from project root."
    exit 1
fi

# Check if Alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "Alembic not found. Installing..."
    pip install alembic
fi

# Change to backend directory
cd backend

# Run migrations
echo "Applying migrations..."
DATABASE_URL=$DATABASE_URL alembic upgrade head

echo "✅ Migrations complete!"
echo ""
echo "To rollback migrations, run:"
echo "  DATABASE_URL=$DATABASE_URL alembic downgrade -1"
