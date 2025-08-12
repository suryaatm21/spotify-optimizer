"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
import logging

# Ensure project root is on sys.path when running as a script from backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Support running as a module (backend.main) and as a script (python main.py in backend/)
try:
    from backend.routers import auth, analytics, clustering, listening_analytics, optimization, crud
except ModuleNotFoundError:
    from routers import auth, analytics, clustering, listening_analytics, optimization, crud

def _configure_logging():
    """Configure logging so our routers/services emit INFO-level logs in dev.
    This complements Uvicorn's own loggers and avoids being filtered at WARNING.
    """
    # Set a sensible default formatter
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%H:%M:%S"

    # Ensure root logger is at least INFO in dev
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt)

    # Explicitly raise log level for our package namespaces
    for name in (
        # Primary package-qualified names
        "backend",
        "backend.routers",
        "backend.services",
        "backend.routers.analytics",
        "backend.services.clustering",
        # Fallback names when importing as scripts (e.g., `from routers import ...`)
        "routers",
        "services",
        "routers.analytics",
        "services.clustering",
    ):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        # If no handlers attached (e.g., not running under uvicorn), add one
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
            logger.addHandler(handler)
        # Avoid duplicate logs if propagated to root
        logger.propagate = True


_configure_logging()

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
app.include_router(clustering.router, prefix="/api", tags=["enhanced-clustering"])
app.include_router(listening_analytics.router, prefix="/api", tags=["listening-analytics"])
app.include_router(optimization.router, prefix="/api", tags=["playlist-optimization"])
app.include_router(crud.router, prefix="/api", tags=["crud"])

@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"message": "Spotify Playlist Optimizer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
