"""
Render Validator API - V2 Golf Course Research Validation Service

Purpose: Validates V2 LLM research JSON and writes to Supabase
Architecture: FastAPI endpoint → V2Validator → Section parsers → Supabase writer

Endpoints:
- POST /validate-and-write: Main validation workflow
- GET /health: Health check

Created: 2025-10-31
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from validator import V2Validator

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Golf V2 Validator",
    description="Validates V2 LLM research JSON and writes to Supabase",
    version="1.0.0"
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ValidationRequest(BaseModel):
    """Request payload from validate-v2-research edge function"""
    staging_id: str = Field(..., description="UUID of llm_research_staging record")
    course_id: Optional[int] = Field(None, description="INTEGER ID of existing course (if updating)")
    course_name: str = Field(..., description="Name of golf course")
    state_code: str = Field(..., description="State code (e.g., NC, VA)")
    v2_json: Dict[str, Any] = Field(..., description="V2 LLM research JSON (5 sections)")

class ValidationResponse(BaseModel):
    """Response payload sent back to edge function"""
    success: bool
    course_id: Optional[int] = None  # INTEGER not UUID (matches golf_courses.id type)
    contacts_created: int = 0
    validation_flags: list[str] = Field(default_factory=list)
    error: Optional[str] = None

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/validate-and-write", response_model=ValidationResponse)
async def validate_and_write(request: ValidationRequest):
    """
    Main validation workflow

    Steps:
    1. Validate V2 JSON structure (CRITICAL validations)
    2. Parse each of 5 sections
    3. Perform quality validations (soft warnings)
    4. Write to golf_courses + golf_course_contacts tables
    5. Return success + validation flags

    CRITICAL validations (hard failures):
    - All 5 sections present
    - Tier field exists with valid value
    - Tier confidence ≥ 0.5
    - At least 1 contact in section 4

    QUALITY validations (soft warnings):
    - Tier confidence < 0.7 → flag LOW_TIER_CONFIDENCE
    - Zero contacts → flag NO_CONTACTS_FOUND
    - No email/LinkedIn on contacts → flag NO_CONTACT_METHODS
    """
    logger.info(f"🚀 Validation request: {request.course_name} ({request.state_code})")
    logger.info(f"   Staging ID: {request.staging_id}")
    logger.info(f"   Course ID: {request.course_id or 'NEW COURSE'}")

    try:
        # Initialize validator
        use_test_tables = os.getenv("USE_TEST_TABLES", "false").lower() == "true"
        validator = V2Validator(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY"),
            use_test_tables=use_test_tables
        )

        # Process validation + database write
        result = await validator.process(
            staging_id=request.staging_id,
            course_id=request.course_id,
            course_name=request.course_name,
            state_code=request.state_code,
            v2_json=request.v2_json
        )

        if not result["success"]:
            logger.error(f"❌ Validation failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"✅ Validation succeeded")
        logger.info(f"   Course ID: {result['course_id']}")
        logger.info(f"   Contacts: {result['contacts_created']}")
        logger.info(f"   Flags: {result['validation_flags']}")

        return ValidationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Render

    Verifies:
    - Service is running
    - Environment variables configured
    - Supabase connection can be established
    """
    health_status = {
        "status": "healthy",
        "service": "golf-v2-validator",
        "version": "1.0.0"
    }

    # Check environment variables
    required_env_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        health_status["status"] = "unhealthy"
        health_status["error"] = f"Missing environment variables: {', '.join(missing_vars)}"
        return JSONResponse(content=health_status, status_code=503)

    health_status["env_vars_configured"] = True

    # TODO: Add Supabase connection test
    # For now, just verify vars are set

    return health_status

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable in production
        log_level="info"
    )
