# 🌳 Children's Thinking Tree System

A web-based interactive thinking tree system designed to help children develop critical thinking and problem-solving skills through visual tree structures and AI-powered guidance.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## ✨ Features

- 🎯 Interactive thinking tree visualization
- 🤖 AI-powered Qwen API integration for real-time audio/text interaction
- 🎨 Beautiful, child-friendly UI with Vue 3 and Nuxt 4
- 🔒 WebSocket proxy for secure API communication
- 📱 Responsive design for all devices
- 🌍 Multi-language support (Chinese/English)

## 🛠 Tech Stack

### Frontend
- **Framework**: Nuxt 4 (Vue 3)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Testing**: Vitest
- **Code Quality**: ESLint + Prettier

### Backend
- **Framework**: FastAPI (Python 3.11)
- **WebSocket**: WebSockets for real-time communication
- **AI Integration**: Qwen Omni API (DashScope)
- **Testing**: pytest
- **Code Quality**: Ruff + Black + mypy

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Vercel (Frontend) / Docker (Backend)

## 📦 Prerequisites

- **Node.js** 20+ (with pnpm)
- **Python** 3.11+
- **Docker** & Docker Compose
- **Git**

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/children-thinking-tree.git
cd children-thinking-tree
```

### 2. Set up environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: DASHSCOPE_API_KEY (from Alibaba Cloud Bailian)
```

### 3. Start development environment

```bash
# Using Docker (recommended)
./scripts/setup-dev.sh

# Or manually
docker-compose up --build
```

### 4. Access the application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8765
- **Health Check**: http://localhost:8765/health

## 🔧 Development Setup

### Without Docker

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.proxy_server:app --reload --port 8765
```

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## 🧪 Testing

### Run All Tests

```bash
./scripts/run-tests.sh
```

### Frontend Tests

```bash
cd frontend
pnpm test:unit          # Run tests
pnpm test:coverage      # Run with coverage
```

### Backend Tests

```bash
cd backend
pytest                   # Run tests
pytest --cov=src         # Run with coverage
```

### Code Quality Checks

```bash
# Frontend
cd frontend
pnpm lint               # Run ESLint
pnpm format:check       # Check Prettier
pnpm typecheck          # Run TypeScript checks

# Backend
cd backend
ruff check .            # Run Ruff linter
black --check .         # Check Black formatting
mypy .                  # Run type checks
```

## 🚢 Deployment

### Frontend (Vercel)

```bash
./scripts/deploy-frontend.sh
```

Or connect your GitHub repo to Vercel for automatic deployments.

### Backend (Docker)

```bash
./scripts/deploy-backend.sh
```

### Database Migrations

```bash
DATABASE_URL="postgresql://user:pass@host/db" ./scripts/migrate-database.sh
```

## 📁 Project Structure

```
tree/
├── frontend/                    # Nuxt 4 frontend
│   ├── components/              # Vue components
│   ├── pages/                   # Nuxt pages
│   ├── composables/             # Vue composables
│   ├── tests/                   # Frontend tests
│   └── Dockerfile               # Frontend Docker config
├── backend/                     # FastAPI backend
│   ├── src/
│   │   └── api/
│   │       └── proxy_server.py  # WebSocket proxy
│   ├── tests/                   # Backend tests
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend Docker config
├── scripts/                     # Deployment & utility scripts
├── docs/                        # Documentation
├── docker-compose.yml           # Docker Compose config
└── .github/workflows/           # CI/CD workflows
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `style:` formatting
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Alibaba Cloud](https://www.alibabacloud.com/) for Qwen API
- [Nuxt](https://nuxt.com/) for the amazing frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) for the powerful backend framework
