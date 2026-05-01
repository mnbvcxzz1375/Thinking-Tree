# Backend Development Guide

## Project Overview

This is a FastAPI backend for the Children's Thinking Tree System. It provides REST APIs for managing activities, tree nodes, speech records, and teacher reviews with PostgreSQL database integration.

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Application (main.py)  │
│  - CORS Middleware                  │
│  - Health Check Endpoints           │
│  - Route Registration               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      API Routers (routers/)         │
│  - Activities CRUD                  │
│  - Tree Nodes CRUD                  │
│  - Error Handling                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Pydantic Schemas (schemas/)       │
│  - Request Validation               │
│  - Response Serialization           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   SQLAlchemy Models (models/)       │
│  - ORM Definitions                  │
│  - Relationships                    │
│  - Indexes                          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Database Layer (database.py)      │
│  - Engine Management                │
│  - Session Factory                  │
│  - Migration Support                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      PostgreSQL Database            │
│  - Activities Table                 │
│  - TreeNodes Table                  │
│  - SpeechRecords Table              │
│  - TeacherReviews Table             │
└─────────────────────────────────────┘
```

## File Structure

```
app/
├── __init__.py              # Package marker
├── main.py                  # FastAPI app initialization
├── config.py                # Configuration management
├── database.py              # Database setup and session
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── activity.py          # Activity model
│   ├── tree_node.py         # TreeNode model
│   ├── speech_record.py     # SpeechRecord model
│   └── teacher_review.py    # TeacherReview model
├── routers/                 # API endpoint handlers
│   ├── __init__.py
│   ├── activities.py        # Activity CRUD endpoints
│   └── tree_nodes.py        # TreeNode CRUD endpoints
└── schemas/                 # Pydantic request/response schemas
    ├── __init__.py
    ├── activity.py          # Activity schemas
    └── tree_node.py         # TreeNode schemas
```

## Development Workflow

### 1. Adding a New Model

Create a new file in `app/models/`:

```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewModel(id={self.id}, name={self.name})>"
```

Update `app/models/__init__.py`:

```python
from app.models.new_model import NewModel
__all__ = ["Activity", "TreeNode", "SpeechRecord", "TeacherReview", "NewModel"]
```

### 2. Adding Schemas

Create schemas in `app/schemas/`:

```python
# app/schemas/new_model.py
from pydantic import BaseModel
from datetime import datetime

class NewModelBase(BaseModel):
    name: str

class NewModelCreate(NewModelBase):
    pass

class NewModelResponse(NewModelBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 3. Adding API Routes

Create router in `app/routers/`:

```python
# app/routers/new_models.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.new_model import NewModel
from app.schemas.new_model import NewModelCreate, NewModelResponse

router = APIRouter()

@router.get("", response_model=List[NewModelResponse])
async def list_new_models(db: Session = Depends(get_db)):
    return db.query(NewModel).all()

@router.post("", response_model=NewModelResponse, status_code=status.HTTP_201_CREATED)
async def create_new_model(model: NewModelCreate, db: Session = Depends(get_db)):
    db_model = NewModel(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model
```

Register in `app/main.py`:

```python
from app.routers import new_models
app.include_router(new_models.router, prefix="/api/new-models", tags=["New Models"])
```

### 4. Database Migrations

After model changes, create a migration:

```bash
alembic revision --autogenerate -m "Add new_models table"
```

Review the generated migration in `migrations/versions/`, then apply:

```bash
alembic upgrade head
```

## Code Style

### Type Hints

Always use type hints:

```python
# Good
def get_activity(activity_id: int, db: Session = Depends(get_db)) -> Activity:
    return db.query(Activity).filter(Activity.id == activity_id).first()

# Bad
def get_activity(activity_id, db):
    return db.query(Activity).filter(Activity.id == activity_id).first()
```

### Docstrings

Use docstrings for functions and classes:

```python
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)) -> Activity:
    """Create a new activity.
    
    Args:
        activity: Activity data to create
        db: Database session
        
    Returns:
        Created activity object
    """
    db_activity = Activity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity
```

### Error Handling

Use appropriate HTTP exceptions:

```python
@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: int, db: Session = Depends(get_db)) -> Activity:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity {activity_id} not found",
        )
    return activity
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_proxy.py

# Run with coverage
pytest --cov=app

# Run with verbose output
pytest -v
```

### Writing Tests

Create test files in `tests/`:

```python
# tests/test_activities.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_activity(client: AsyncClient):
    response = await client.post(
        "/api/activities",
        json={
            "title": "Test Activity",
            "description": "Test",
            "difficulty_level": "easy"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Activity"
```

## Code Quality

### Linting

```bash
# Check code style
ruff check .

# Fix issues automatically
ruff check . --fix
```

### Formatting

```bash
# Check formatting
black --check .

# Format code
black .
```

### Type Checking

```bash
# Run type checker
mypy .
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Configuration

### Environment Variables

All configuration is in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/thinking_tree
DATABASE_ECHO=false

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

### Settings Class

Configuration is managed in `app/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://..."
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## Database Operations

### Creating Records

```python
# Create and save
activity = Activity(
    title="New Activity",
    description="Description",
    difficulty_level="medium"
)
db.add(activity)
db.commit()
db.refresh(activity)
```

### Querying Records

```python
# Get all
activities = db.query(Activity).all()

# Filter
activity = db.query(Activity).filter(Activity.id == 1).first()

# With relationships
activity = db.query(Activity).filter(Activity.id == 1).first()
tree_nodes = activity.tree_nodes  # Access related data
```

### Updating Records

```python
activity = db.query(Activity).filter(Activity.id == 1).first()
activity.title = "Updated Title"
db.add(activity)
db.commit()
db.refresh(activity)
```

### Deleting Records

```python
activity = db.query(Activity).filter(Activity.id == 1).first()
db.delete(activity)
db.commit()
```

## Common Tasks

### Add a New Endpoint

1. Create schema in `app/schemas/`
2. Create model in `app/models/` (if needed)
3. Create router in `app/routers/`
4. Register router in `app/main.py`
5. Create migration if model changed
6. Write tests in `tests/`

### Modify Database Schema

1. Update model in `app/models/`
2. Create migration: `alembic revision --autogenerate -m "Description"`
3. Review migration file
4. Apply: `alembic upgrade head`

### Add Validation

Use Pydantic validators:

```python
from pydantic import BaseModel, field_validator

class ActivityCreate(BaseModel):
    title: str
    difficulty_level: str
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ['easy', 'medium', 'hard']:
            raise ValueError('Invalid difficulty level')
        return v
```

### Add Relationships

In models:

```python
class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True)
    # ... other columns
    
    # One-to-many relationship
    tree_nodes = relationship("TreeNode", back_populates="activity")

class TreeNode(Base):
    __tablename__ = "tree_nodes"
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    
    # Back reference
    activity = relationship("Activity", back_populates="tree_nodes")
```

## Debugging

### Enable SQL Logging

In `.env`:

```env
DATABASE_ECHO=true
```

This will print all SQL queries to console.

### Debug Mode

In `.env`:

```env
DEBUG=true
```

This enables FastAPI debug mode and auto-reload.

### Print Statements

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Activity created: {activity.id}")
logger.error(f"Error: {e}")
```

## Performance Tips

1. **Use indexes** - Add indexes to frequently queried columns
2. **Eager loading** - Use `joinedload()` for relationships
3. **Pagination** - Limit query results with `skip` and `limit`
4. **Connection pooling** - Configure in production
5. **Caching** - Cache frequently accessed data

## Deployment

### Docker

```bash
docker build -t thinking-tree-backend .
docker run -p 8765:8765 --env-file .env thinking-tree-backend
```

### Production Server

Use Gunicorn:

```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:
1. Check the README.md
2. Review the QUICKSTART.md
3. Check FastAPI docs at `/docs`
4. Review code comments and docstrings
