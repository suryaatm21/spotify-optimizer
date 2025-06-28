import sys
import os
from sqlalchemy import inspect

# Add the backend directory to the Python path
# This allows us to import modules like 'database' and 'models' directly
sys.path.insert(0, os.path.dirname(__file__))

from database import engine
from models import Base  # Import Base to ensure models are registered

def verify_database_schema():
    """
    Connects to the database defined in the application and inspects its schema.
    Prints a list of all tables found.
    """
    print(f"Attempting to connect to database: {engine.url}")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("\n[ERROR] No tables were found in the database.")
            print("This likely means the schema was not created correctly.")
            print("Please ensure 'backend/models.py' contains your SQLAlchemy model definitions and that 'create_db.py' is running without errors.")
        else:
            print("\n[SUCCESS] Found the following tables:")
            for table_name in tables:
                print(f"- {table_name}")
                
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred while inspecting the database: {e}")

if __name__ == "__main__":
    verify_database_schema()
