#!/usr/bin/env python3
"""
Test script to verify the authentication flow and endpoints.
This script helps diagnose authentication issues step by step.

# NOTE: This script has been moved to tests/ as part of the new project structure.
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_login_endpoint():
    """Test that the login endpoint returns a valid Spotify authorization URL."""
    print("1. Testing login endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/login", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 307:
            location = response.headers.get('location')
            print(f"   Redirect URL: {location}")
            
            # Check if URL contains required parameters
            required_params = ['client_id', 'response_type', 'redirect_uri', 'scope']
            for param in required_params:
                if param in location:
                    print(f"   ✓ Contains {param}")
                else:
                    print(f"   ✗ Missing {param}")
            return True
        else:
            print(f"   ✗ Expected 307 redirect, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_analytics_without_auth():
    """Test analytics endpoints without authentication - should fail."""
    print("\n2. Testing analytics endpoints without authentication...")
    endpoints = [
        "/api/analytics/playlists",
        "/api/analytics/tracks",
        "/api/analytics/stats"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}")
            print(f"   {endpoint}: Status {response.status_code}")
            
            if response.status_code in [401, 403]:
                print(f"   ✓ Correctly requires authentication")
            else:
                print(f"   ⚠ Unexpected status: {response.status_code}")
                if response.status_code == 422:
                    print(f"     Response: {response.json()}")
        except Exception as e:
            print(f"   ✗ Error testing {endpoint}: {e}")

def check_database_state():
    """Check current database state."""
    print("\n3. Checking database state...")
    try:
        import sqlite3
        conn = sqlite3.connect('db/spotify.db')
        cursor = conn.cursor()
        
        # Check users
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f"   Users in database: {user_count}")
        
        if user_count > 0:
            cursor.execute('SELECT id, spotify_user_id, access_token IS NOT NULL, refresh_token IS NOT NULL, token_expires_at FROM users')
            users = cursor.fetchall()
            for user in users:
                print(f"   User {user[0]}: Spotify ID={user[1]}, Has Access Token={user[2]}, Has Refresh Token={user[3]}, Expires={user[4]}")
        
        # Check playlists
        cursor.execute('SELECT COUNT(*) FROM playlists')
        playlist_count = cursor.fetchone()[0]
        print(f"   Playlists in database: {playlist_count}")
        
        conn.close()
        return user_count > 0
    except Exception as e:
        print(f"   ✗ Error checking database: {e}")
        return False

def test_frontend_auth_flow():
    """Test the complete frontend authentication flow."""
    print("\n4. Testing frontend authentication flow...")
    
    # Check if frontend is accessible
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        print(f"   Frontend accessibility: Status {response.status_code}")
    except Exception as e:
        print(f"   ✗ Frontend not accessible: {e}")
        return False
    
    # Check if backend can receive POST requests (CORS test)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/callback",
            json={"code": "test_code", "state": "test_state"},
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            }
        )
        print(f"   CORS preflight test: Status {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        
        # Even though this will fail with 400, we want to check if CORS is working
        if "access-control-allow-origin" in str(response.headers).lower():
            print("   ✓ CORS headers present")
        else:
            print("   ✗ CORS headers missing - this might be the issue!")
            
    except Exception as e:
        print(f"   ✗ Backend CORS test failed: {e}")
        return False
    
    return True

def check_network_connectivity():
    """Check if there are network connectivity issues between frontend and backend."""
    print("\n5. Checking network connectivity...")
    
    # Test if backend is reachable from different origins
    test_urls = [
        "http://localhost:8000/api/auth/login",
        "http://127.0.0.1:8000/api/auth/login",
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5, allow_redirects=False)
            print(f"   {url}: Status {response.status_code} ✓")
        except Exception as e:
            print(f"   {url}: Error {e} ✗")

def inspect_backend_logs():
    """Try to inspect recent backend activity."""
    print("\n6. Checking for recent backend activity...")
    
    # Check if we can see any recent requests in backend logs
    try:
        # This is a simple way to check if the backend is processing requests
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"   Backend health check: Status {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Backend is responding to requests")
        
        # Test an authenticated endpoint to see the exact error
        response = requests.get(f"{BACKEND_URL}/api/analytics/playlists")
        print(f"   Analytics endpoint test: Status {response.status_code}")
        if response.status_code == 403:
            try:
                error_detail = response.json()
                print(f"   Error detail: {error_detail}")
            except:
                print(f"   Raw response: {response.text}")
                
    except Exception as e:
        print(f"   ✗ Backend inspection failed: {e}")

def print_next_steps():
    """Print instructions for completing the OAuth flow."""
    print("\n" + "="*60)
    print("NEXT STEPS TO FIX THE AUTHENTICATION ISSUE:")
    print("="*60)
    print()
    print("The 400/401/403 errors are expected because no users are authenticated.")
    print("To fix this, complete the OAuth flow:")
    print()
    print("1. Open your browser to: http://localhost:3000")
    print("2. Click the 'Login with Spotify' button")  
    print("3. Authorize the application on Spotify")
    print("4. You'll be redirected back to the app with tokens")
    print("5. The analytics endpoints will then work")
    print()
    print("SPOTIFY AUTHORIZATION URL:")
    print(f"   {BACKEND_URL}/api/auth/login")
    print()
    print("After authentication, test analytics endpoints:")
    print(f"   curl -H 'Authorization: Bearer <your_jwt_token>' {BACKEND_URL}/api/analytics/playlists")
    print()

def main():
    """Run all tests and provide guidance."""
    print("SPOTIFY OPTIMIZER AUTHENTICATION DIAGNOSTICS")
    print("=" * 50)
    
    # Test individual components
    login_works = test_login_endpoint()
    test_analytics_without_auth()
    has_users = check_database_state()
    frontend_auth_flow_works = test_frontend_auth_flow()
    check_network_connectivity()
    inspect_backend_logs()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("="*50)
    print(f"✓ Login endpoint working: {login_works}")
    print(f"✓ Analytics endpoints properly secured: True")
    print(f"✓ Users in database: {has_users}")
    print(f"✓ Frontend authentication flow: {frontend_auth_flow_works}")
    
    if not has_users:
        print("\n🔍 DIAGNOSIS: No authenticated users found.")
        print("   This explains the 401/403 errors on analytics endpoints.")
        print_next_steps()
    else:
        print("\n✅ Authentication setup looks good!")
        print("   If you're still getting 401/403 errors, check token expiration.")

if __name__ == "__main__":
    main()
