#!/usr/bin/env python3
"""
Real-time OAuth flow tester.
This script will monitor the callback process in real-time.

# NOTE: This script has been moved to db/ as part of the new project structure.
"""
import time
import requests
import sqlite3
from datetime import datetime

def monitor_oauth_flow():
    """Monitor the OAuth flow completion in real-time."""
    print("🔍 REAL-TIME OAUTH FLOW MONITOR")
    print("=" * 50)
    print()
    print("1. Visit this URL to start OAuth:")
    print("   http://localhost:3000")
    print()
    print("2. Click 'Login with Spotify'")
    print()
    print("3. Complete authorization on Spotify")
    print()
    print("4. This script will monitor for user creation...")
    print()
    print("Monitoring database for new users...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    last_user_count = 0
    monitoring_start = datetime.now()
    
    try:
        while True:
            # Check database for new users
            try:
                conn = sqlite3.connect('spotify.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                current_user_count = cursor.fetchone()[0]
                
                if current_user_count != last_user_count:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🎉 USER COUNT CHANGED: {last_user_count} → {current_user_count}")
                    
                    if current_user_count > 0:
                        # Get user details
                        cursor.execute('SELECT spotify_user_id, display_name, email, created_at FROM users ORDER BY id DESC LIMIT 1')
                        user = cursor.fetchone()
                        print(f"           New user: {user[1]} ({user[0]})")
                        print(f"           Email: {user[2]}")
                        print(f"           Created: {user[3]}")
                        print()
                        print("✅ SUCCESS! User created successfully!")
                        print("Now testing analytics endpoints...")
                        
                        # Test analytics endpoint
                        try:
                            response = requests.get("http://localhost:8000/api/analytics/playlists")
                            print(f"Analytics endpoint test: Status {response.status_code}")
                            if response.status_code == 403:
                                print("⚠️  Still getting 403 - need to use JWT token from frontend")
                            elif response.status_code == 200:
                                print("🎉 Analytics endpoint working!")
                        except Exception as e:
                            print(f"Analytics test error: {e}")
                        
                        break
                    
                    last_user_count = current_user_count
                
                conn.close()
                
                # Show periodic status
                if int(time.time()) % 10 == 0:  # Every 10 seconds
                    elapsed = datetime.now() - monitoring_start
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Monitoring... ({int(elapsed.total_seconds())}s elapsed, {current_user_count} users)")
                
            except Exception as e:
                print(f"Database check error: {e}")
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        print("If no users were created, check browser console for JavaScript errors.")

if __name__ == "__main__":
    monitor_oauth_flow()
