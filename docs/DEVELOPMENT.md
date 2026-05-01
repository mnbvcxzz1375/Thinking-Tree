# Development Workflow Guide

## Getting Started

### Prerequisites

Ensure you have the following installed:
- Node.js 20+ with pnpm
- Python 3.11+
- Docker & Docker Compose
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/children-thinking-tree.git
   cd children-thinking-tree
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start the development environment:
   ```bash
   ./scripts/setup-dev.sh
   ```

## Development Workflow

### Daily Development

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Make your changes**:
   - Frontend: Edit files in `frontend/`
   - Backend: Edit files in `backend/`

4. **Run tests**:
   ```bash
   ./scripts/run-tests.sh
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature
   ```

### Code Style

#### Frontend (TypeScript/Vue)
- ESLint for linting
- Prettier for formatting
- Run `pnpm lint:fix` to auto-fix issues

#### Backend (Python)
- Ruff for linting
- Black for formatting
- mypy for type checking
- Run `ruff check --fix .` to auto-fix

### Git Workflow

1. Create feature branch from `develop`
2. Make changes with conventional commits
3. Push and create PR
4. PR triggers CI checks
5. Merge after review and CI passes

## Debugging

### Frontend

```bash
cd frontend
pnpm dev  # Starts dev server with HMR
```

### Backend

```bash
cd backend
uvicorn src.api.proxy_server:app --reload --log-level debug
```

### Docker

```bash
docker-compose logs -f frontend  # Frontend logs
docker-compose logs -f backend   # Backend logs
docker-compose down              # Stop all
```

## IDE Setup

### VS Code

Install recommended extensions:
- ESLint
- Prettier
- Python
- Volar (Vue)
- Docker

Settings are included in `.vscode/settings.json` (if present).

### JetBrains

Import the project settings from `.idea/` directory.
