# Children's Thinking Tree - Backend API

FastAPI-based backend for the children's thinking tree system with PostgreSQL database and AI integration.

## Features

- ✅ FastAPI framework with async support
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Database migrations with Alembic
- ✅ CORS middleware configuration
- ✅ Comprehensive error handling
- ✅ RESTful API endpoints
- ✅ Connection pooling and health checks
- ✅ Docker support for development and production

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database setup and session management
│   ├── exceptions.py           # Custom exception classes
│   ├── models/                 # SQLAlchemy models
│   │   ├── activity.py
│   │   ├── tree_node.py
│   │   ├── speech_record.py
│   │   ├── teacher_review.py
│   │   └── suggestion.py
│   ├── schemas/                # Pydantic schemas for request/response
│   ├── routers/                # API route handlers
│   │   ├── activities.py
│   │   ├── tree_nodes.py
│   │   ├── activity_nodes.py
│   │   ├── export.py
│   │   ├── suggestions.py
│   │   ├── questions.py
│   │   └── stats.py
│   └── services/               # Business logic services
├── migrations/                 # Alembic database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── tests/                      # Test files
├── pyproject.toml              # Project configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Database Schema

### Tables

1. **activities** - Thinking tree activities
   - id, title, description, instructions, difficulty_level, age_group, is_active, created_at, updated_at

2. **tree_nodes** - Nodes in the thinking tree
   - id, activity_id, parent_id, content, node_type, position_x, position_y, created_at, updated_at

3. **speech_records** - Speech interaction records
   - id, activity_id, tree_node_id, user_input, ai_response, audio_url, duration_seconds, confidence_score, created_at

4. **teacher_reviews** - Teacher feedback on nodes
   - id, tree_node_id, teacher_name, feedback, rating, is_approved, created_at, updated_at

5. **suggestions** - AI-generated suggestions
   - id, activity_id, tree_node_id, suggestion_text, suggestion_type, confidence_score, is_resolved, created_at, updated_at

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /api/status` - API status with configuration

### Activities
- `GET /api/activities` - List all activities
- `GET /api/activities/{activity_id}` - Get activity details
- `POST /api/activities` - Create new activity
- `PUT /api/activities/{activity_id}` - Update activity
- `DELETE /api/activities/{activity_id}` - Delete activity

### Tree Nodes
- `GET /api/nodes` - List tree nodes
- `GET /api/nodes/{node_id}` - Get node details
- `POST /api/nodes` - Create new node
- `PUT /api/nodes/{node_id}` - Update node
- `DELETE /api/nodes/{node_id}` - Delete node
- `POST /api/nodes/{node_id}/move` - Move node to new parent

### Activity Nodes
- `GET /api/activities/{activity_id}/nodes` - Get activity's nodes
- `GET /api/activities/{activity_id}/nodes/tree` - Get tree structure
- `POST /api/activities/{activity_id}/nodes` - Create node in activity

### Data Export/Import
- `POST /api/data/export` - Export activity data
- `POST /api/data/import` - Import activity data
- `POST /api/data/export/png` - Export as PNG
- `POST /api/data/export/pdf` - Export as PDF
- `GET /api/data/export/markdown/{activity_id}` - Export as Markdown
- `GET /api/data/export/json/{activity_id}` - Export as JSON

### Suggestions
- `POST /api/suggestions/analyze/{activity_id}` - Analyze and generate suggestions
- `GET /api/suggestions/{activity_id}` - Get suggestions for activity
- `GET /api/suggestions/{activity_id}/pending` - Get pending suggestions
- `PUT /api/suggestions/{suggestion_id}/resolve` - Resolve suggestion

### Questions
- `POST /api/questions/generate` - Generate follow-up questions
- `POST /api/questions/empty-branch` - Generate questions for empty branches
- `POST /api/questions/deep-exploration` - Generate deep exploration questions
- `POST /api/questions/connect` - Generate connection questions

### Statistics
- `GET /api/stats/overview` - Overall statistics
- `GET /api/stats/activities/{activity_id}` - Activity statistics
- `GET /api/stats/activities/{activity_id}/insights` - Activity insights

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
   ```

   API will be available at: http://localhost:8765
   API docs at: http://localhost:8765/docs

### Docker Development

1. **From project root:**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Access services:**
   - Backend API: http://localhost:8765
   - Frontend: http://localhost:3000
   - PostgreSQL: localhost:5432

## Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/thinking_tree
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Server
HOST=127.0.0.1
PORT=8765
DEBUG=false

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# AI API
DASHSCOPE_API_KEY=your_api_key
QWEN_MODEL=qwen3.5-omni-flash-realtime
QWEN_REGION=cn

# Audio
AUDIO_SAMPLE_RATE=16000
AUDIO_BIT_DEPTH=16
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=3200
```

## Database Migrations

### Create new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app
```

### Run specific test file
```bash
pytest tests/test_activities.py
```

## Code Quality

### Format code
```bash
black app/
```

### Lint code
```bash
ruff check app/
```

### Type checking
```bash
mypy app/
```

## Deployment

### Production Build
```bash
docker build -t thinking-tree-api:latest --target production .
```

### Run Production Container
```bash
docker run -p 8765:8765 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/thinking_tree \
  -e DASHSCOPE_API_KEY=your_key \
  thinking-tree-api:latest
```

## Troubleshooting

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check DATABASE_URL in .env
3. Ensure database exists: `createdb thinking_tree`
4. Test connection: `psql $DATABASE_URL`

### Migration Errors
1. Check migration files in `migrations/versions/`
2. Verify database state: `alembic current`
3. Reset database (development only): `alembic downgrade base`

### API Not Starting
1. Check Python version: `python --version` (should be 3.11+)
2. Verify dependencies: `pip list | grep fastapi`
3. Check for syntax errors: `python -m py_compile app/main.py`

## Performance Optimization

- Connection pooling configured with QueuePool
- Database indexes on frequently queried columns
- Async/await for non-blocking operations
- Response caching headers configured
- CORS middleware optimized

## Security

- CORS properly configured
- SQL injection prevention via SQLAlchemy ORM
- Input validation with Pydantic
- Error handling without exposing sensitive info
- Environment variables for secrets

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes and test: `pytest`
3. Format code: `black app/`
4. Lint: `ruff check app/`
5. Commit: `git commit -m "feat: description"`
6. Push and create PR

## License

MIT License - See LICENSE file for details
