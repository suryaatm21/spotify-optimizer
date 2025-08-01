#!/usr/bin/env python3
"""
Test database connection to troubleshoot OperationalError.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.dependencies import get_database, DATABASE_URL
from backend.models import User
from sqlalchemy.orm import Session

def test_database():
    """Test database connection and table access."""
    print(f"Database URL: {DATABASE_URL}")
    
    try:
        # Get database session
        db_gen = get_database()
        db: Session = next(db_gen)
        
        # Try to query users table
        users = db.query(User).all()
        print(f"Successfully queried users table. Found {len(users)} users.")
        
        # Try to create a test user (we'll delete it afterwards)
        test_user = User(
            spotify_user_id="test_user_123",
            display_name="Test User",
            access_token="test_token"
        )
        db.add(test_user)
        db.commit()
        print("Successfully created test user.")
        
        # Delete the test user
        db.delete(test_user)
        db.commit()
        print("Successfully deleted test user.")
        
        print("✅ Database connection test PASSED!")
        
    except Exception as e:
        print(f"❌ Database connection test FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    test_database()
