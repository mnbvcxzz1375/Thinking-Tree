"""FastAPI main application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from app.config import settings
from app.database import init_db
from app.exceptions import AppException, NotFoundError, ValidationError, DatabaseError
from app.routers import activities, tree_nodes, activity_nodes, export, suggestions, questions, stats, auth, audio_proxy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Children's Thinking Tree API",
    description="API for AI-powered thinking tree system",
    version="1.0.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url),
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "NotFound",
            "message": exc.message,
            "path": str(request.url),
        },
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": exc.message,
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": str(request.url),
        },
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    logger.info("Starting up FastAPI application")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down FastAPI application")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "thinking-tree-api",
    }


@app.get("/api/status", tags=["Status"])
async def api_status() -> dict[str, object]:
    """API status endpoint."""
    return {
        "provider": "qwen",
        "model": settings.qwen_model,
        "region": settings.qwen_region,
        "audio_config": {
            "sample_rate": settings.audio_sample_rate,
            "bit_depth": settings.audio_bit_depth,
            "channels": settings.audio_channels,
        },
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
app.include_router(
    activity_nodes.router, prefix="/api/activities", tags=["Activity Nodes"]
)
app.include_router(tree_nodes.router, prefix="/api/nodes", tags=["Tree Nodes"])
app.include_router(export.router, prefix="/api/data", tags=["Data Export/Import"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(questions.router, prefix="/api/questions", tags=["Follow-up Questions"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(audio_proxy.router, tags=["Audio Proxy"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
