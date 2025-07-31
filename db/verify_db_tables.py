#!/usr/bin/env python3
"""
Verify database tables exist in the correct location.
"""
import sqlite3
from pathlib import Path

# Check the main database location
db_path = Path("db/spotify.db")
print(f"Checking database at: {db_path.absolute()}")

if not db_path.exists():
    print("❌ Database file does not exist!")
    exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\n✅ Database found with {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} records")
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_table = cursor.fetchone()
    
    if users_table:
        print("\n✅ Users table exists")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   Users count: {user_count}")
    else:
        print("\n❌ Users table does NOT exist")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error accessing database: {e}")
    exit(1)

print("\n✅ Database verification complete")
