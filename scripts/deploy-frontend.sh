#!/bin/bash
# Frontend deployment script for Vercel/Netlify

set -e

echo "🚀 Deploying frontend..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Deploy to Vercel
echo "Deploying to Vercel..."
cd frontend
vercel --prod

echo "✅ Frontend deployment complete!"
