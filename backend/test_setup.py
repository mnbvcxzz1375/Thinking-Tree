#!/usr/bin/env python
"""Test script to verify backend setup."""

from app.database import Base
from app.models.activity import Activity
from app.models.tree_node import TreeNode
from app.models.speech_record import SpeechRecord
from app.models.teacher_review import TeacherReview
from app.main import app
from app.config import settings

print("=" * 60)
print("Backend Configuration Test")
print("=" * 60)

# Test configuration
print("\n1. Configuration:")
print(f"   Host: {settings.host}")
print(f"   Port: {settings.port}")
print(f"   Debug: {settings.debug}")
print(f"   Database URL: {settings.database_url}")
print(f"   CORS Origins: {settings.cors_origins}")

# Test FastAPI app
print("\n2. FastAPI Application:")
print(f"   Title: {app.title}")
print(f"   Version: {app.version}")
print(f"   Routes: {len(app.routes)}")

# Test database schema
print("\n3. Database Schema:")
print(f"   Tables: {len(Base.metadata.tables)}")
for table_name in Base.metadata.tables:
    table = Base.metadata.tables[table_name]
    print(f"   - {table_name} ({len(table.columns)} columns)")

# Test models
print("\n4. Models:")
models = [Activity, TreeNode, SpeechRecord, TeacherReview]
for model in models:
    print(f"   - {model.__name__}")

# Test routers
print("\n5. API Routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', set())
        if methods:
            print(f"   {', '.join(sorted(methods))} {route.path}")

print("\n" + "=" * 60)
print("All tests passed!")
print("=" * 60)
