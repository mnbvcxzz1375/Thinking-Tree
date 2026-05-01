# FastAPI Backend - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection string
```

### Step 3: Create Database

```bash
# Using psql
createdb thinking_tree

# Or using your database client
```

### Step 4: Initialize Database Tables

```bash
# Option A: Using Python
python -c "from app.database import init_db; init_db()"

# Option B: Using Alembic
alembic upgrade head
```

### Step 5: Run the Server

```bash
uvicorn app.main:app --reload
```

Server will be available at: `http://localhost:8765`

## Verify Installation

### Health Check

```bash
curl http://localhost:8765/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-05-01T00:00:00.000000",
  "service": "thinking-tree-api"
}
```

### API Status

```bash
curl http://localhost:8765/api/status
```

Expected response:
```json
{
  "provider": "qwen",
  "model": "qwen3.5-omni-flash-realtime",
  "region": "cn",
  "audio_config": {
    "sample_rate": 16000,
    "bit_depth": 16,
    "channels": 1
  }
}
```

## Test API Endpoints

### Create an Activity

```bash
curl -X POST http://localhost:8765/api/activities \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Critical Thinking Exercise",
    "description": "Learn to think critically",
    "difficulty_level": "medium",
    "age_group": "8-12"
  }'
```

### List Activities

```bash
curl http://localhost:8765/api/activities
```

### Create a Tree Node

```bash
curl -X POST http://localhost:8765/api/tree-nodes \
  -H "Content-Type: application/json" \
  -d '{
    "activity_id": 1,
    "content": "What is the main problem?",
    "node_type": "question"
  }'
```

### List Tree Nodes

```bash
curl http://localhost:8765/api/tree-nodes
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

## Common Issues

### psycopg2 Not Found

```bash
pip install psycopg2-binary
```

### Database Connection Failed

Check your `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/thinking_tree
```

Verify PostgreSQL is running:
```bash
psql -U user -d thinking_tree -c "SELECT 1"
```

### Port 8765 Already in Use

Change port in `.env`:
```env
PORT=8766
```

Or run with different port:
```bash
uvicorn app.main:app --port 8766
```

## Next Steps

1. Read the full [README.md](./README.md) for detailed documentation
2. Check [API Endpoints](#api-endpoints) section
3. Review database schema in [Database Schema](#database-schema)
4. Set up pre-commit hooks: `pre-commit install`
5. Run tests: `pytest`

## Project Structure

```
app/
├── main.py           # FastAPI app
├── config.py         # Configuration
├── database.py       # Database setup
├── models/           # ORM models
├── routers/          # API endpoints
└── schemas/          # Request/response schemas
```

## Environment Variables

Key variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://... | PostgreSQL connection |
| HOST | 127.0.0.1 | Server host |
| PORT | 8765 | Server port |
| DEBUG | false | Debug mode |
| DASHSCOPE_API_KEY | - | Qwen API key |

See `.env.example` for all options.

## Database Models

- **Activity** - Thinking tree activities
- **TreeNode** - Nodes in the tree structure
- **SpeechRecord** - Speech interactions
- **TeacherReview** - Teacher feedback

## API Routes

### Activities
- `GET /api/activities` - List
- `POST /api/activities` - Create
- `GET /api/activities/{id}` - Get
- `PUT /api/activities/{id}` - Update
- `DELETE /api/activities/{id}` - Delete

### Tree Nodes
- `GET /api/tree-nodes` - List
- `POST /api/tree-nodes` - Create
- `GET /api/tree-nodes/{id}` - Get
- `PUT /api/tree-nodes/{id}` - Update
- `DELETE /api/tree-nodes/{id}` - Delete

## Development Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Code quality checks
ruff check .
black .
mypy .

# Format code
black app/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Docker

```bash
# Build
docker build -t thinking-tree-backend .

# Run
docker run -p 8765:8765 --env-file .env thinking-tree-backend
```

## Support

For issues or questions, refer to:
- Full [README.md](./README.md)
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
