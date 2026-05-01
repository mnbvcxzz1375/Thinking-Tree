#!/bin/bash
# Backend development setup script

set -e

echo "🔧 Setting up backend development environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment if not exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv backend/venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create .env file if not exists
if [ ! -f backend/.env ]; then
    echo "Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env file with your database credentials"
fi

echo ""
echo "✅ Backend development environment is ready!"
echo ""
echo "🔧 Useful commands:"
echo "   source backend/venv/bin/activate          # Activate virtual environment"
echo "   cd backend && python -m pytest            # Run tests"
echo "   cd backend && uvicorn app.main:app --reload  # Start development server"
echo "   cd backend && alembic upgrade head        # Run database migrations"
