#!/usr/bin/env python3
"""
Startup script for the Spotify Playlist Optimizer backend.
Sets up the Python path and starts the FastAPI server.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path so backend module can be imported
backend_dir = Path(__file__).parent.absolute()
parent_dir = backend_dir.parent
sys.path.insert(0, str(parent_dir))

# Now we can import with absolute paths
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Spotify Playlist Optimizer API...")
    print("📍 Backend directory:", backend_dir)
    print("🔗 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
