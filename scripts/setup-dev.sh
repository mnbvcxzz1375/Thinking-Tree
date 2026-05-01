#!/bin/bash
# Development environment setup script

set -e

echo "🔧 Setting up development environment..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Copy environment file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys"
fi

# Build and start containers
echo "Building and starting containers..."
docker-compose up --build -d

# Wait for services
echo "Waiting for services to start..."
sleep 5

# Check health
echo "Checking service health..."
curl -f http://localhost:8765/health || echo "Backend health check failed"

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📡 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8765"
echo ""
echo "🔧 Useful commands:"
echo "   docker-compose logs -f        # View logs"
echo "   docker-compose down           # Stop services"
echo "   docker-compose restart        # Restart services"
