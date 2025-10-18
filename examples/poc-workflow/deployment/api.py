#!/usr/bin/env python3
"""
FastAPI wrapper for Agent 7 (Water Hazard Counter)
Deployment POC for Claude Agent SDK on Render

Endpoints:
- GET  /         - Service info
- GET  /health   - Health check (for Render)
- POST /count-hazards - Count water hazards on a golf course
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sys
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# Import Agent 7
try:
    from agent7_water_hazard_counter import count_water_hazards
    logger.info("Successfully imported Agent 7")
except ImportError as e:
    logger.error(f"Failed to import Agent 7: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="Golf Course Water Hazard API",
    description="Agent 7 - Count water hazards on golf courses using Perplexity AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response Models
class CourseRequest(BaseModel):
    """Request body for water hazard counting"""
    course_name: str = Field(..., description="Name of the golf course")
    state: str = Field(..., description="State where the course is located (e.g., 'VA', 'Virginia')")
    website: str | None = Field(None, description="Optional course website URL for better search context")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "course_name": "Richmond Country Club",
                    "state": "VA",
                    "website": "https://www.richmondcountryclubva.com/"
                }
            ]
        }
    }


class CourseResponse(BaseModel):
    """Response with water hazard count and metadata"""
    water_hazard_count: int | None = Field(..., description="Number of water hazards found (1-18), or null if not found")
    confidence: str = Field(..., description="Confidence level: 'high', 'medium', 'low', or 'none'")
    details: list[str] = Field(..., description="Details about the water hazards found")
    query_approach: str = Field(..., description="Query approach used: 'direct', 'scorecard', or 'failed'")
    cost: float = Field(..., description="Cost of the query in USD")
    found: bool = Field(..., description="Whether water hazards were found")

    # Optional debug info
    approach1_count: int | None = None
    approach1_confidence: str | None = None
    approach2_count: int | None = None
    approach2_confidence: str | None = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str | None = None
    timestamp: str


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=type(exc).__name__,
            detail=str(exc),
            timestamp=datetime.utcnow().isoformat()
        ).model_dump()
    )


# Endpoints
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Golf Course Water Hazard Counter",
        "agent": "Agent 7",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "count_hazards": "POST /count-hazards",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        },
        "description": "Count water hazards on golf courses using Perplexity AI search",
        "cost_per_query": "$0.006 avg",
        "response_time": "8-15 seconds avg"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Render and monitoring

    Returns:
        dict: Health status with timestamp
    """
    return {
        "status": "healthy",
        "service": "agent7-water-hazards",
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "Agent 7",
        "dependencies": {
            "claude_cli": "installed",  # Verified during container build
            "perplexity_api": "configured"
        }
    }


@app.post("/count-hazards", response_model=CourseResponse)
async def count_hazards(request: CourseRequest):
    """
    Count water hazards on a golf course

    This endpoint uses Agent 7 to search for water hazard information using
    Perplexity AI. It tries multiple query approaches to find the most accurate count.

    Args:
        request: CourseRequest with course_name, state, and optional website

    Returns:
        CourseResponse with water hazard count and confidence level

    Raises:
        HTTPException: If the query fails or environment is not configured
    """
    logger.info(f"Received request for: {request.course_name}, {request.state}")

    try:
        # Call Agent 7
        result = await count_water_hazards(
            course_name=request.course_name,
            state=request.state,
            website=request.website
        )

        logger.info(
            f"Agent 7 completed: {request.course_name} - "
            f"Found: {result.get('water_hazard_count')}, "
            f"Confidence: {result.get('confidence')}, "
            f"Cost: ${result.get('cost', 0):.4f}"
        )

        return CourseResponse(**result)

    except KeyError as e:
        # Missing environment variable
        logger.error(f"Missing environment variable: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server configuration error: {str(e)}"
        )

    except Exception as e:
        # Other errors
        logger.error(f"Agent 7 error for {request.course_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to count water hazards: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("="*70)
    logger.info("🌊 Agent 7 Water Hazard API Starting...")
    logger.info("="*70)
    logger.info(f"Service: Golf Course Water Hazard Counter")
    logger.info(f"Agent: Agent 7")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("="*70)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Agent 7 API shutting down...")


if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
