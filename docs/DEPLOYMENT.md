# Deployment Guide

## Overview

This project supports deployment via:
- **Frontend**: Vercel (recommended) or Netlify
- **Backend**: Docker container on any cloud provider

## Prerequisites

- Vercel account (for frontend)
- Cloud provider account (AWS, GCP, Azure, etc.)
- Docker installed locally
- Domain name (optional)

## Frontend Deployment (Vercel)

### Option 1: Automatic Deployment

1. Push your code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import your GitHub repository
4. Configure settings:
   - Framework Preset: Nuxt
   - Root Directory: `frontend`
   - Build Command: `pnpm build`
   - Output Directory: `.output/public`
5. Add environment variables
6. Deploy

### Option 2: Manual Deployment

```bash
./scripts/deploy-frontend.sh
```

### Environment Variables

Add these to Vercel:
```
NUXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Backend Deployment (Docker)

### Build and Push Image

```bash
# Build image
docker build -t tree-backend:latest ./backend

# Tag for registry
docker tag tree-backend:latest ghcr.io/your-org/tree-backend:latest

# Push to GitHub Container Registry
docker push ghcr.io/your-org/tree-backend:latest
```

### Deploy to Cloud Provider

#### AWS ECS

1. Create ECS cluster
2. Create task definition with your image
3. Create service
4. Configure load balancer

#### Google Cloud Run

```bash
gcloud run deploy tree-backend \
  --image ghcr.io/your-org/tree-backend:latest \
  --port 8765 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
az container create \
  --name tree-backend \
  --resource-group myResourceGroup \
  --image ghcr.io/your-org/tree-backend:latest \
  --ports 8765 \
  --environment-variables DASHSCOPE_API_KEY=your-key
```

### Environment Variables

Set these on your cloud provider:
```
DASHSCOPE_API_KEY=your-api-key
QWEN_MODEL=qwen3.5-omni-flash-realtime
QWEN_REGION=cn
HOST=0.0.0.0
PORT=8765
```

## Database Deployment

### PostgreSQL (Recommended)

1. Create database on your cloud provider
2. Set `DATABASE_URL` environment variable
3. Run migrations:
   ```bash
   DATABASE_URL="postgresql://user:pass@host/db" ./scripts/migrate-database.sh
   ```

## SSL/TLS Configuration

### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

### Using Cloudflare

1. Add your domain to Cloudflare
2. Enable SSL/TLS encryption
3. Create DNS records pointing to your server

## Monitoring

### Health Checks

- Frontend: `https://your-domain.com`
- Backend: `https://your-api-domain.com/health`

### Logging

- AWS: CloudWatch Logs
- GCP: Cloud Logging
- Azure: Azure Monitor

## Rollback

### Frontend (Vercel)

1. Go to Vercel dashboard
2. Select your project
3. Go to Deployments
4. Find previous deployment
5. Click "Promote to Production"

### Backend (Docker)

```bash
# Pull previous version
docker pull ghcr.io/your-org/tree-backend:previous-tag

# Update service
docker service update --image ghcr.io/your-org/tree-backend:previous-tag tree-backend
```

## Troubleshooting

### Common Issues

1. **Backend not starting**: Check logs with `docker logs <container-id>`
2. **API key errors**: Verify environment variables are set correctly
3. **WebSocket connection failed**: Ensure CORS is configured properly

### Support

- Check [GitHub Issues](https://github.com/your-org/children-thinking-tree/issues)
- Contact: support@your-domain.com
