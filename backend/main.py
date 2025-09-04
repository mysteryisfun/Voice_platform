"""
FastAPI application setup and configuration
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import get_db, create_tables
from routes import health, agents, onboarding, data_processing

# Filter out health check logs
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/api/health" not in record.getMessage()

# Apply filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

# Create FastAPI app
app = FastAPI(
    title="Voice Agent Platform API",
    description="AI-powered platform for creating and deploying conversational voice agents",
    version="0.1.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(onboarding.router, prefix="/api", tags=["onboarding"])
app.include_router(data_processing.router, prefix="/api/data", tags=["data-processing"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    create_tables()
    print("Database tables created successfully")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
