"""Test script to verify FastAPI app initialization."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports without database connection
    from app.config import settings

    print("[OK] Config imported successfully")
    print(f"[OK] Database URL: {settings.database_url}")
    print(f"[OK] Server: {settings.host}:{settings.port}")
    print(f"[OK] Debug mode: {settings.debug}")
    print(f"[OK] CORS origins: {settings.cors_origins}")
    print(f"[OK] AI Model: {settings.qwen_model}")

    # Test models can be imported
    from app.models.activity import Activity
    from app.models.tree_node import TreeNode
    from app.models.speech_record import SpeechRecord
    from app.models.teacher_review import TeacherReview

    print("[OK] All models imported successfully")

    # Test schemas can be imported
    from app.schemas.activity import ActivityCreate, ActivityResponse
    from app.schemas.tree_node import TreeNodeCreate, TreeNodeResponse

    print("[OK] All schemas imported successfully")

    # Test routers can be imported
    from app.routers import activities, tree_nodes

    print("[OK] All routers imported successfully")

    print("\n[SUCCESS] All checks passed!")
    print("\nNote: Database connection requires psycopg2 to be installed.")
    print("Install with: pip install -r requirements.txt")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
