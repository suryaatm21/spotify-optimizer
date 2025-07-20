#!/usr/bin/env python3
"""
Test script to help debug the OAuth callback step by step.

# NOTE: This script has been moved to db/ as part of the new project structure.
"""
import webbrowser
import time

def debug_oauth_flow():
    """Guide through OAuth debugging step by step."""
    print("🔍 OAUTH CALLBACK DEBUGGING GUIDE")
    print("=" * 50)
    print()
    
    print("The issue is likely one of these:")
    print()
    
    print("1. 🚫 CLICKING 'CANCEL' ON SPOTIFY")
    print("   - If you click 'Cancel' instead of 'Authorize', Spotify redirects to homepage")
    print("   - Make sure to click the GREEN 'Agree' button on Spotify")
    print()
    
    print("2. 🔄 FRONTEND ERROR HANDLING")
    print("   - If OAuth code exchange fails, frontend redirects to homepage")
    print("   - Check browser console for error messages")
    print()
    
    print("3. 🌐 BROWSER COMPATIBILITY")
    print("   - Some browsers block OAuth redirects")
    print("   - Try in Chrome/Firefox instead of VS Code browser")
    print()
    
    print("STEP-BY-STEP TEST:")
    print("-" * 20)
    print()
    
    print("1. Open this URL in your REGULAR browser (not VS Code):")
    print("   https://accounts.spotify.com/authorize?client_id=da2391ba0fd8492eb4547b2e27680d16&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A3000%2Fcallback&scope=user-read-private+playlist-read-private+playlist-modify-public+playlist-modify-private+user-library-read+user-library-modify+user-read-playback-state+user-read-recently-played+user-top-read+user-read-email+user-read-playback-position&state=random_state_string")
    print()
    
    print("2. On Spotify authorization page:")
    print("   ✅ Click the GREEN 'Agree' button")
    print("   ❌ Do NOT click 'Cancel' or close the window")
    print()
    
    print("3. Watch the URL bar carefully:")
    print("   - Should redirect to: http://127.0.0.1:3000/callback?code=...")
    print("   - If it goes to http://127.0.0.1:3000/ instead, you clicked Cancel")
    print()
    
    print("4. Open browser console (F12) immediately:")
    print("   - Look for any error messages")
    print("   - Take a screenshot of any errors")
    print()
    
    print("5. If you see the callback URL with ?code=, the issue is in frontend processing")
    print("   If you only see homepage, the issue is in Spotify authorization")
    print()
    
    input("Press Enter when you're ready to test...")
    
    print("Opening authorization URL in your default browser...")
    auth_url = "https://accounts.spotify.com/authorize?client_id=da2391ba0fd8492eb4547b2e27680d16&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A3000%2Fcallback&scope=user-read-private+playlist-read-private+playlist-modify-public+playlist-modify-private+user-library-read+user-library-modify+user-read-playback-state+user-read-recently-played+user-top-read+user-read-email+user-read-playback-position&state=random_state_string"
    
    webbrowser.open(auth_url)
    
    print()
    print("🔍 Now watch carefully:")
    print("1. Click the GREEN 'Agree' button on Spotify")
    print("2. Watch the URL change")
    print("3. Check browser console for errors")
    print("4. Report back what you see!")

if __name__ == "__main__":
    debug_oauth_flow()
