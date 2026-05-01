# FastAPI Backend - Children's Thinking Tree System

## Overview

This is the FastAPI backend for the Children's Thinking Tree System. It provides REST APIs for managing activities, tree nodes, speech records, and teacher reviews, with PostgreSQL database integration.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database setup and session management
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── activity.py         # Activity model
│   │   ├── tree_node.py        # TreeNode model
│   │   ├── speech_record.py    # SpeechRecord model
│   │   └── teacher_review.py   # TeacherReview model
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── activities.py       # Activity CRUD endpoints
│   │   └── tree_nodes.py       # TreeNode CRUD endpoints
│   └── schemas/                # Pydantic request/response schemas
│       ├── __init__.py
│       ├── activity.py
│       └── tree_node.py
├── migrations/                 # Alembic database migrations
│   ├── __init__.py
│   ├── env.py
│   ├── script.py.mako
│   ├── alembic.ini
│   └── versions/
│       └── 001_initial.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_proxy.py
├── .env.example                # Environment variables template
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── Dockerfile                  # Docker configuration
├── pyproject.toml              # Project configuration (Ruff, Black, MyPy, Pytest)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip or conda

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the environment template and update with your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/thinking_tree
DATABASE_ECHO=false

# Server
HOST=127.0.0.1
PORT=8765
DEBUG=false

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# AI API
DASHSCOPE_API_KEY=your-api-key-here
QWEN_MODEL=qwen3.5-omni-flash-realtime
QWEN_REGION=cn
```

### 4. Initialize Database

Create the PostgreSQL database:

```bash
createdb thinking_tree
```

Run migrations:

```bash
alembic upgrade head
```

Or use the Python API to initialize tables:

```python
from app.database import init_db
init_db()
```

### 5. Run the Server

Development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

Production mode:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765 --workers 4
```

The API will be available at `http://localhost:8765`

## API Endpoints

### Health Check

- `GET /health` - Health check endpoint
- `GET /api/status` - API status and configuration

### Activities

- `GET /api/activities` - List all activities
- `GET /api/activities/{activity_id}` - Get activity by ID
- `POST /api/activities` - Create new activity
- `PUT /api/activities/{activity_id}` - Update activity
- `DELETE /api/activities/{activity_id}` - Delete activity

### Tree Nodes

- `GET /api/tree-nodes` - List tree nodes (optionally filtered by activity)
- `GET /api/tree-nodes/{node_id}` - Get tree node by ID
- `POST /api/tree-nodes` - Create new tree node
- `PUT /api/tree-nodes/{node_id}` - Update tree node
- `DELETE /api/tree-nodes/{node_id}` - Delete tree node

## Database Schema

### Activities Table

Stores thinking tree activities.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String(255) | Activity title |
| description | Text | Activity description |
| instructions | Text | Instructions for the activity |
| difficulty_level | String(50) | Difficulty level (easy, medium, hard) |
| age_group | String(50) | Target age group |
| is_active | Boolean | Whether activity is active |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### TreeNodes Table

Represents nodes in the thinking tree structure.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| activity_id | Integer | Foreign key to activities |
| parent_id | Integer | Foreign key to parent tree node |
| content | Text | Node content/question |
| node_type | String(50) | Type (question, answer, insight) |
| position_x | Integer | X coordinate for visualization |
| position_y | Integer | Y coordinate for visualization |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### SpeechRecords Table

Stores speech interactions and AI responses.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| activity_id | Integer | Foreign key to activities |
| tree_node_id | Integer | Foreign key to tree nodes |
| user_input | Text | User's spoken input |
| ai_response | Text | AI's response |
| audio_url | String(500) | URL to audio file |
| duration_seconds | Float | Duration of speech |
| confidence_score | Float | Confidence score of recognition |
| created_at | DateTime | Creation timestamp |

### TeacherReviews Table

Stores teacher feedback on tree nodes.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| tree_node_id | Integer | Foreign key to tree nodes |
| teacher_name | String(255) | Teacher's name |
| feedback | Text | Feedback content |
| rating | Integer | Rating (1-5 stars) |
| is_approved | Integer | Approval status (0: pending, 1: approved, -1: rejected) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

Run specific test file:

```bash
pytest tests/test_proxy.py
```

## Code Quality

### Linting

```bash
ruff check .
```

### Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

Run hooks manually:

```bash
pre-commit run --all-files
```

## Docker

Build Docker image:

```bash
docker build -t thinking-tree-backend .
```

Run container:

```bash
docker run -p 8765:8765 --env-file .env thinking-tree-backend
```

## Configuration

All configuration is managed through environment variables in `.env` file. See `.env.example` for all available options.

### Key Settings

- `DATABASE_URL` - PostgreSQL connection string
- `HOST` - Server host (default: 127.0.0.1)
- `PORT` - Server port (default: 8765)
- `DEBUG` - Debug mode (default: false)
- `CORS_ORIGINS` - Allowed CORS origins
- `DASHSCOPE_API_KEY` - Qwen API key
- `QWEN_MODEL` - AI model name
- `QWEN_REGION` - API region (cn or intl)

## Logging

Logging is configured in `app/main.py`. Logs are output to console with INFO level by default.

## Database Migrations

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

## Development Workflow

1. Create a new branch for your feature
2. Make changes to models, routes, or schemas
3. Write tests for new functionality
4. Run code quality checks:
   ```bash
   ruff check .
   black .
   mypy .
   pytest
   ```
5. Commit changes with conventional commit messages
6. Push and create a pull request

## Troubleshooting

### Database Connection Error

Ensure PostgreSQL is running and the `DATABASE_URL` is correct:

```bash
psql postgresql://user:password@localhost:5432/thinking_tree
```

### Module Not Found Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Port Already in Use

Change the port in `.env` or use:

```bash
uvicorn app.main:app --port 8766
```

## Contributing

See the main project README for contribution guidelines.

## License

MIT License - See LICENSE file for details
