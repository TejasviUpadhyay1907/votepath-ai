"""VotePath AI Backend - Main application entry point"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.services.startup_service import get_startup_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting VotePath AI Backend...")
    startup_service = get_startup_service()
    summary = startup_service.initialize_application()
    app.state.startup_mode = summary["mode"]
    app.state.sheets_loaded = summary["sheets_loaded"]
    logger.info(f"Application ready in {summary['mode']} mode")
    yield
    logger.info("Shutting down VotePath AI Backend...")


app = FastAPI(
    title="VotePath AI Backend",
    version="1.0.0",
    description="Election Process Education Assistant – rule-based, deterministic, reliable.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# API routes
app.include_router(router)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/ui", include_in_schema=False)
async def serve_frontend():
    """Serve the frontend SPA"""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=False)

