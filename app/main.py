"""VotePath AI Backend - Main application entry point"""

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import router
from app.services.startup_service import get_startup_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # requests
RATE_LIMIT_WINDOW = 60  # seconds


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client has exceeded rate limit.

    Args:
        client_ip: Client IP address

    Returns:
        bool: True if request is allowed, False if rate limit exceeded
    """
    now = time.time()
    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    # Check limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    # Add new request
    rate_limit_store[client_ip].append(now)
    return True


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting VotePath AI Backend...")
    startup_service = get_startup_service()
    summary = startup_service.initialize_application()
    application.state.startup_mode = summary["mode"]
    application.state.sheets_loaded = summary["sheets_loaded"]
    logger.info("Application ready in %s mode", summary['mode'])
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


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    # Skip rate limiting in test environment
    settings = get_settings()
    if settings.ENVIRONMENT == "test":
        response = await call_next(request)
        return response

    client_ip = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    response = await call_next(request)
    return response


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

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
