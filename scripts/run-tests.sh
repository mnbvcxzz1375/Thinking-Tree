#!/bin/bash
# Run all tests

set -e

echo "🧪 Running tests..."

# Frontend tests
echo ""
echo "=== Frontend Tests ==="
cd frontend
if [ -f "package.json" ]; then
    pnpm test:unit
fi
cd ..

# Backend tests
echo ""
echo "=== Backend Tests ==="
cd backend
if [ -f "requirements.txt" ]; then
    pytest --cov=src --cov-report=html
fi
cd ..

echo ""
echo "✅ All tests complete!"
echo "📊 Coverage reports:"
echo "   Frontend: frontend/coverage/"
echo "   Backend:  backend/htmlcov/"
