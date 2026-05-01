#!/bin/bash
# Quick start backend development server

set -e

echo "🚀 Starting backend development server..."

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Run setup-backend.sh first."
    exit 1
fi

# Activate virtual environment
source backend/venv/bin/activate

# Change to backend directory
cd backend

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head || echo "⚠️  Migration warning (database might not be ready)"

# Start development server
echo ""
echo "✅ Starting FastAPI development server..."
echo "📡 API available at: http://localhost:8765"
echo "📚 API docs at: http://localhost:8765/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
