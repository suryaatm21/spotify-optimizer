"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, analytics, listening_analytics, optimization

app = FastAPI(
    title="Spotify Playlist Optimizer API",
    description="API for analyzing and optimizing Spotify playlists using machine learning clustering",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(listening_analytics.router, prefix="/api", tags=["listening-analytics"])
app.include_router(optimization.router, prefix="/api", tags=["playlist-optimization"])

@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"message": "Spotify Playlist Optimizer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
