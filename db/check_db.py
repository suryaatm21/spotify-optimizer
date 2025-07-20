#!/usr/bin/env python3
"""
Standalone database verification script for the Spotify Playlist Optimizer.
This script is completely self-contained and doesn't rely on any project imports.
"""
import sqlite3
import os

def check_database():
    """
    Check if the SQLite database exists and inspect its schema.
    """
    db_path = "db/spotify.db"
    
    print(f"Checking database at: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print("\n[ERROR] Database file does not exist!")
        print("Please run 'python backend/create_db.py' to create the database first.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("\n[ERROR] No tables found in the database!")
            print("The database file exists but contains no tables.")
            print("Please run 'python backend/create_db.py' to create the schema.")
        else:
            print(f"\n[SUCCESS] Found {len(tables)} table(s):")
            for table in tables:
                table_name = table[0]
                print(f"- {table_name}")
                
                # Get column info for each table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                if columns:
                    print(f"  Columns: {', '.join([col[1] for col in columns])}")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"  Rows: {count}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Failed to inspect database: {e}")

if __name__ == "__main__":
    check_database()
