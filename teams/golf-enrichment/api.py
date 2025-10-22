#!/usr/bin/env python3
"""
FastAPI wrapper for Golf Course Enrichment Pipeline
Full orchestrator with all 8 agents

Endpoints:
- GET  /         - Service info
- GET  /health   - Health check (for Render)
- POST /count-hazards - Count water hazards (Agent 7 only)
- POST /enrich-course - Full pipeline (Agents 1-8)
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sys
import os
from pathlib import Path
from datetime import datetime
import logging
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# Import Agent 7 (for backwards compatibility)
try:
    from agent7_water_hazard_counter import count_water_hazards
    logger.info("Successfully imported Agent 7")
except ImportError as e:
    logger.error(f"Failed to import Agent 7: {e}")
    raise

# Import Orchestrator (full pipeline)
try:
    from orchestrator import enrich_course as orchestrator_enrich_course
    logger.info("Successfully imported Orchestrator")
except ImportError as e:
    logger.error(f"Failed to import Orchestrator: {e}")
    raise


# Webhook to Supabase Edge Function
async def send_enrichment_webhook(course_id: int, result: dict) -> None:
    """
    Send enrichment webhook to trigger ClickUp sync

    NOTE: Agent 8 already wrote all data to database.
    This webhook ONLY triggers ClickUp task creation.
    Edge function reads fresh data from database.

    Args:
        course_id: ID from golf_courses table (written by Agent 8)
        result: Orchestrator result (only need success flag + identifiers)
    """
    webhook_url = "https://oadmysogtfopkbmrulmq.supabase.co/functions/v1/receive-agent-enrichment"

    # Minimal payload - edge function reads from database
    payload = {
        'course_id': course_id,
        'success': result.get('success', False),
        'course_name': result.get('course_name'),
        'state_code': result.get('state_code')
    }

    # Get Supabase anon key for authorization
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_anon_key:
        logger.error("❌ SUPABASE_ANON_KEY not set - webhook will fail")
        return

    headers = {
        "Authorization": f"Bearer {supabase_anon_key}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Webhook sent successfully for course_id={course_id}")
    except httpx.HTTPError as e:
        logger.error(f"❌ Webhook failed for course_id={course_id}: {e}")
        # Don't raise - webhook failure shouldn't fail the enrichment
    except Exception as e:
        logger.error(f"❌ Unexpected webhook error for course_id={course_id}: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Golf Course Enrichment API",
    description="Full pipeline: Agents 1-8 for golf course and contact data enrichment",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response Models

# Agent 7 (Water Hazards) Models
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


# Orchestrator (Full Pipeline) Models
class EnrichCourseRequest(BaseModel):
    """Request body for full course enrichment (Agents 1-8)"""
    course_name: str = Field(..., description="Name of the golf course")
    state_code: str = Field(default="VA", description="State code (e.g., 'VA', 'DC', 'MD')")
    course_id: int | None = Field(None, description="Optional: Course ID to update (ensures correct course is enriched, avoids name mismatch issues)")
    use_test_tables: bool = Field(default=True, description="Use test Supabase tables (true) or production (false)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "course_name": "Richmond Country Club",
                    "state_code": "VA",
                    "course_id": 108,
                    "use_test_tables": True
                }
            ]
        }
    }


class EnrichCourseResponse(BaseModel):
    """Response with full enrichment results"""
    success: bool
    course_name: str
    state_code: str
    json_file: str | None
    summary: dict
    error: str | None = None
    agent_results: dict


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
        "service": "Golf Course Enrichment Pipeline",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "count_hazards": "POST /count-hazards (Agent 7 only)",
            "test_agent8": "POST /test-agent8 (Test Agent 8 in isolation)",
            "enrich_course": "POST /enrich-course (Full pipeline: Agents 1-8)",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        },
        "description": "Complete golf course enrichment with 8 specialized agents",
        "agents": {
            "agent1": "URL Finder",
            "agent2": "Data Extractor",
            "agent3": "Email + LinkedIn Finder",
            "agent5": "Phone Finder",
            "agent6": "Course Intelligence",
            "agent6.5": "Contact Background",
            "agent7": "Water Hazard Counter",
            "agent8": "Supabase Writer"
        },
        "cost_per_course": "$0.155 avg (with 3 contacts)",
        "response_time": "2-3 minutes avg"
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


@app.post("/test-agent8")
async def test_agent8():
    """
    Test Agent 8 (Supabase Writer) in isolation

    This endpoint tests Agent 8's ability to write to Supabase without
    running the full enrichment pipeline. Useful for debugging database
    connection and schema issues.

    Returns:
        dict: Agent 8 result with success status, course_id, and contacts_written
    """
    logger.info("🧪 Testing Agent 8 in isolation...")

    try:
        from agent8_supabase_writer import write_to_supabase

        # Minimal test data
        test_course_data = {
            "data": {
                "course_name": "Test Course (API Agent 8)",
                "website": "https://testcourse.com",
                "phone": "804-555-9999"
            }
        }

        test_course_intel = {
            "segmentation": {
                "primary_target": "budget",  # Valid segment value
                "confidence": 7,
                "signals": ["API test data"]
            },
            "range_intel": {"has_range": True},
            "opportunities": {
                "range_ball_buy": 5,
                "range_ball_lease": 5
            }
        }

        test_water_data = {
            "water_hazard_count": 3,
            "confidence": "medium",
            "details": ["API test"]
        }

        test_contacts = [
            {
                "name": "API Test Contact",
                "title": "Test Manager",
                "email": "test@testcourse.com",
                "email_confidence": 50,
                "email_method": "api_test",
                "phone": "804-555-8888",
                "method": "api_test",
                "confidence": 50,
                "background": {
                    "tenure_years": None,
                    "tenure_confidence": "unknown",
                    "previous_clubs": [],
                    "industry_experience_years": None,
                    "responsibilities": ["Test duty"],
                    "career_notes": "API test contact"
                }
            }
        ]

        # Call Agent 8 directly
        result = await write_to_supabase(
            test_course_data,
            test_course_intel,
            test_water_data,
            test_contacts,
            state_code="VA",
            use_test_tables=False  # Write to production tables
        )

        logger.info(
            f"✅ Agent 8 test completed - "
            f"Success: {result.get('success')}, "
            f"Course ID: {result.get('course_id')}, "
            f"Contacts: {result.get('contacts_written')}"
        )

        return {
            "test": "agent8",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
            "note": "Test course created in production database. Clean up manually if needed."
        }

    except Exception as e:
        logger.error(f"Agent 8 test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent 8 test failed: {str(e)}"
        )


@app.post("/enrich-course", response_model=EnrichCourseResponse)
async def enrich_course(request: EnrichCourseRequest):
    """
    Run full enrichment pipeline (Agents 1-8)

    This endpoint executes all 8 agents in sequence:
    1. Agent 1: Find course URL
    2. Agent 2: Extract course data + staff contacts
    3. Agent 6: Course intelligence (segment, opportunities)
    4. Agent 7: Count water hazards
    5. For each contact:
       - Agent 3: Find email + LinkedIn
       - Agent 5: Find phone number
       - Agent 6.5: Contact background (tenure, previous clubs)
    6. Agent 8: Write to Supabase

    Args:
        request: EnrichCourseRequest with course_name, state_code, use_test_tables

    Returns:
        EnrichCourseResponse with full pipeline results

    Raises:
        HTTPException: If any agent fails
    """
    logger.info(f"🏌️ Full enrichment requested for: {request.course_name}, {request.state_code}")

    try:
        # Call Orchestrator
        result = await orchestrator_enrich_course(
            course_name=request.course_name,
            state_code=request.state_code,
            course_id=request.course_id,
            use_test_tables=request.use_test_tables
        )

        logger.info(
            f"✅ Orchestrator completed: {request.course_name} - "
            f"Success: {result.get('success')}, "
            f"Contacts: {result.get('summary', {}).get('contacts_enriched', 0)}, "
            f"Cost: ${result.get('summary', {}).get('total_cost_usd', 0):.4f}"
        )

        # Send webhook to Supabase (if course_id available from Agent 8)
        if result.get('course_id'):
            course_id = result['course_id']
            await send_enrichment_webhook(course_id, result)
        else:
            logger.warning(f"No course_id in result - webhook not sent for {request.course_name}")

        return EnrichCourseResponse(**result)

    except Exception as e:
        logger.error(f"Orchestrator error for {request.course_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enrichment pipeline failed: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("="*70)
    logger.info("🏌️ Golf Course Enrichment API Starting...")
    logger.info("="*70)
    logger.info(f"Service: Full Enrichment Pipeline (Agents 1-8)")
    logger.info(f"Version: 2.0.0")
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
