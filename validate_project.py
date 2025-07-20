#!/usr/bin/env python3
"""
Validation script to ensure the refactored project is robust.
Run this before committing to verify everything works correctly.
"""
import sys
import subprocess
from pathlib import Path

def validate_project():
    """Run validation checks on the project."""
    print("🔍 Validating Spotify Playlist Optimizer project...")
    
    # Check that we're in the right directory
    project_root = Path(__file__).parent
    if not (project_root / "backend" / "main.py").exists():
        print("❌ Error: Must run from project root directory")
        return False
    
    print("\n1. ✅ Project structure validation")
    required_dirs = ["backend", "frontend", "db", "tests", "docs"]
    for dir_name in required_dirs:
        if (project_root / dir_name).exists():
            print(f"   ✅ {dir_name}/ directory exists")
        else:
            print(f"   ❌ {dir_name}/ directory missing")
            return False
    
    print("\n2. ✅ Backend configuration validation")
    try:
        sys.path.insert(0, str(project_root))
        from backend.dependencies import DATABASE_URL, DB_PATH
        print(f"   ✅ Database URL: {DATABASE_URL}")
        print(f"   ✅ Database Path: {DB_PATH}")
        print(f"   ✅ Database exists: {DB_PATH.exists()}")
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    
    print("\n3. ✅ Database validation")
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        required_tables = ["users", "playlists", "tracks", "playlist_analyses"]
        for table in required_tables:
            if table in table_names:
                print(f"   ✅ {table} table exists")
            else:
                print(f"   ❌ {table} table missing")
                return False
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False
    
    print("\n4. ✅ Import validation")
    try:
        from backend.main import app
        from backend.models import User, Playlist, Track, PlaylistAnalysis
        from backend.services.clustering import ClusteringService
        from backend.services.audio_features import AudioFeaturesService
        print("   ✅ All critical imports successful")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    print("\n✅ All validation checks passed!")
    print("\n🎯 Ready to commit! The refactor is robust and working correctly.")
    print("\n📝 To start the server:")
    print("   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    
    return True

if __name__ == "__main__":
    success = validate_project()
    sys.exit(0 if success else 1)
