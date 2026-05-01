"""Database configuration and session management with connection pooling."""
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
from app.config import settings

# Base class for all models
Base = declarative_base()

# Lazy-loaded engine and session factory
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def get_engine() -> Engine:
    """Get or create database engine with connection pooling."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=QueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency for FastAPI."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def check_db_health() -> bool:
    """Check if database connection is healthy."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(conn.exec_driver_sql("SELECT 1"))
        return True
    except Exception:
        return False
