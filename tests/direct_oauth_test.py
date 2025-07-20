#!/usr/bin/env python3
"""
Direct OAuth test - bypasses frontend entirely.
This will help us determine if the issue is with the frontend or backend.

# NOTE: This script has been moved to tests/ as part of the new project structure.
"""
import requests
import webbrowser
import time
from urllib.parse import urlparse, parse_qs
import sqlite3

def test_direct_oauth():
    """Test OAuth flow directly without frontend interference."""
    print("🔍 DIRECT OAUTH TEST (BYPASSING FRONTEND)")
    print("=" * 50)
    print()
    
    # Step 1: Get authorization URL
    print("1. Getting authorization URL...")
    response = requests.get('http://localhost:8000/api/auth/login', allow_redirects=False)
    if response.status_code != 307:
        print(f"❌ Failed to get auth URL: {response.status_code}")
        return
    
    auth_url = response.headers.get('location')
    print(f"✅ Auth URL: {auth_url}")
    print()
    
    # Step 2: Open browser for user authorization
    print("2. Opening browser for authorization...")
    print("   You will be redirected to Spotify for authorization.")
    print("   After authorization, you'll be redirected to the callback URL.")
    print("   COPY THE ENTIRE CALLBACK URL and paste it when prompted.")
    print()
    
    webbrowser.open(auth_url)
    
    # Step 3: Get callback URL from user
    print("Waiting for callback URL...")
    callback_url = input("Paste the full callback URL here: ").strip()
    
    if not callback_url.startswith('http://127.0.0.1:3000/callback'):
        print("❌ Invalid callback URL format")
        return
    
    # Step 4: Parse the callback URL to extract code
    parsed_url = urlparse(callback_url)
    query_params = parse_qs(parsed_url.query)
    
    if 'code' not in query_params:
        print("❌ No authorization code found in callback URL")
        if 'error' in query_params:
            print(f"   Spotify error: {query_params['error'][0]}")
        return
    
    code = query_params['code'][0]
    state = query_params.get('state', [''])[0]
    
    print(f"✅ Extracted code: {code[:20]}...")
    print(f"✅ Extracted state: {state}")
    print()
    
    # Step 5: Exchange code for tokens via backend
    print("3. Exchanging code for tokens...")
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/callback',
            json={'code': code, 'state': state},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            jwt_token = token_data.get('access_token')
            print(f"✅ SUCCESS! JWT Token: {jwt_token[:20]}...")
            
            # Step 6: Test authenticated request
            print()
            print("4. Testing authenticated analytics request...")
            auth_response = requests.get(
                'http://localhost:8000/api/analytics/playlists',
                headers={'Authorization': f'Bearer {jwt_token}'}
            )
            print(f"   Analytics Status: {auth_response.status_code}")
            print(f"   Analytics Response: {auth_response.text}")
            
            if auth_response.status_code == 200:
                print("🎉 COMPLETE SUCCESS! OAuth flow working perfectly!")
            else:
                print("⚠️  OAuth works but analytics endpoint still has issues")
            
            # Step 7: Check database
            print()
            print("5. Checking database...")
            conn = sqlite3.connect('db/spotify.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            print(f"   Users in database: {user_count}")
            
            if user_count > 0:
                cursor.execute('SELECT spotify_user_id, display_name FROM users ORDER BY id DESC LIMIT 1')
                user = cursor.fetchone()
                print(f"   Latest user: {user[1]} ({user[0]})")
            
            conn.close()
            
        else:
            print(f"❌ Token exchange failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Raw error: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_direct_oauth()
