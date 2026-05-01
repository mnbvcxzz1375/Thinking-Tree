# FastAPI Backend - Documentation Index

## Quick Navigation

### 🚀 Getting Started
- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute setup guide
  - Installation steps
  - Configuration
  - Verification
  - Common issues

### 📚 Full Documentation
- **[README.md](./README.md)** - Complete documentation
  - Project overview
  - Setup instructions
  - API endpoints
  - Database schema
  - Testing
  - Code quality
  - Docker
  - Troubleshooting

### 👨‍💻 Development
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Development guide
  - Architecture overview
  - File structure
  - Development workflow
  - Code style
  - Testing guide
  - Common tasks
  - Debugging tips

### ✅ Implementation Details
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - What was built
  - Completed tasks
  - How to use
  - Key features
  - Database schema
  - Configuration options

- **[CHECKLIST.md](./CHECKLIST.md)** - Completion checklist
  - All tasks completed
  - Project structure
  - API endpoints
  - Database tables
  - Configuration options

## Project Structure

```
backend/
├── app/                        # Main application package
│   ├── main.py                # FastAPI app
│   ├── config.py              # Configuration
│   ├── database.py            # Database setup
│   ├── models/                # ORM models
│   │   ├── activity.py
│   │   ├── tree_node.py
│   │   ├── speech_record.py
│   │   └── teacher_review.py
│   ├── routers/               # API endpoints
│   │   ├── activities.py
│   │   └── tree_nodes.py
│   └── schemas/               # Pydantic schemas
│       ├── activity.py
│       └── tree_node.py
├── migrations/                # Database migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       └── 001_initial.py
├── tests/                     # Test suite
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
└── [Documentation files]
```

## Key Files

### Application Core
| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/config.py` | Configuration management |
| `app/database.py` | Database setup and session management |

### Database
| File | Purpose |
|------|---------|
| `app/models/activity.py` | Activity model |
| `app/models/tree_node.py` | TreeNode model |
| `app/models/speech_record.py` | SpeechRecord model |
| `app/models/teacher_review.py` | TeacherReview model |
| `migrations/versions/001_initial.py` | Initial database migration |

### API
| File | Purpose |
|------|---------|
| `app/routers/activities.py` | Activity CRUD endpoints |
| `app/routers/tree_nodes.py` | TreeNode CRUD endpoints |
| `app/schemas/activity.py` | Activity request/response schemas |
| `app/schemas/tree_node.py` | TreeNode request/response schemas |

### Configuration
| File | Purpose |
|------|---------|
| `.env.example` | Environment variables template |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Project configuration |

## Quick Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL connection

# Initialize database
python -c "from app.database import init_db; init_db()"
```

### Development
```bash
# Run server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Code quality checks
ruff check .
black .
mypy .
```

### Database
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /api/status` - API status

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

## Database Models

### Activity
- Stores thinking tree activities
- Relationships: tree_nodes, speech_records
- Indexes: is_active, created_at

### TreeNode
- Represents nodes in tree structure
- Relationships: activity, children, speech_records, teacher_reviews
- Indexes: activity_id, parent_id, created_at

### SpeechRecord
- Stores speech interactions
- Relationships: activity, tree_node
- Indexes: activity_id, tree_node_id, created_at

### TeacherReview
- Stores teacher feedback
- Relationships: tree_node
- Indexes: tree_node_id, is_approved, created_at

## Configuration

All settings are in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/thinking_tree

# Server
HOST=127.0.0.1
PORT=8765
DEBUG=false

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# AI API
DASHSCOPE_API_KEY=your-key
QWEN_MODEL=qwen3.5-omni-flash-realtime
```

See `.env.example` for all options.

## Documentation by Topic

### Getting Started
1. Read [QUICKSTART.md](./QUICKSTART.md)
2. Install dependencies
3. Configure `.env`
4. Initialize database
5. Run server

### Development
1. Read [DEVELOPMENT.md](./DEVELOPMENT.md)
2. Understand architecture
3. Follow code style
4. Write tests
5. Check code quality

### API Usage
1. Check [README.md](./README.md) API section
2. Use Swagger UI at `/docs`
3. Use ReDoc at `/redoc`
4. Test with curl or Postman

### Database
1. Review database schema in [README.md](./README.md)
2. Check models in `app/models/`
3. Review migrations in `migrations/`
4. Use Alembic for changes

### Deployment
1. Read [README.md](./README.md) Docker section
2. Build image: `docker build -t thinking-tree-backend .`
3. Run container: `docker run -p 8765:8765 --env-file .env thinking-tree-backend`

## Support Resources

### Official Documentation
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/docs/)

### Interactive API Docs
- Swagger UI: `http://localhost:8765/docs`
- ReDoc: `http://localhost:8765/redoc`

### Project Documentation
- [README.md](./README.md) - Full documentation
- [QUICKSTART.md](./QUICKSTART.md) - Quick setup
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Development guide
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - What was built
- [CHECKLIST.md](./CHECKLIST.md) - Completion checklist

## Status

✅ **READY FOR DEVELOPMENT**

All components are implemented and verified:
- FastAPI application
- PostgreSQL database
- 4 database models
- 2 API routers
- Pydantic validation
- Alembic migrations
- Comprehensive documentation
- Error handling
- Type hints
- Code quality tools

## Next Steps

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Update `.env` with your PostgreSQL connection
3. **Initialize**: `python -c "from app.database import init_db; init_db()"`
4. **Run**: `uvicorn app.main:app --reload`
5. **Test**: Visit `http://localhost:8765/docs`
6. **Develop**: Follow [DEVELOPMENT.md](./DEVELOPMENT.md)

---

**Last Updated**: 2026-05-01
**Status**: Complete ✅
**Version**: 1.0.0
