#!/bin/bash
# Backend deployment script

set -e

echo "🚀 Deploying backend..."

# Build Docker image
echo "Building Docker image..."
docker build -t tree-backend:latest ./backend

# Tag for registry
echo "Tagging image..."
docker tag tree-backend:latest ghcr.io/your-org/tree-backend:latest

# Push to registry
echo "Pushing to registry..."
docker push ghcr.io/your-org/tree-backend:latest

echo "✅ Backend image pushed to registry!"
echo "Deploy to your server with: docker pull ghcr.io/your-org/tree-backend:latest"
