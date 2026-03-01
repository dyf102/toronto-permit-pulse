import os
import httpx
import logging
from fastapi import HTTPException, UploadFile, Form
from typing import Optional

logger = logging.getLogger(__name__)

# Security Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit for PDFs
ALLOWED_EXTENSIONS = {".pdf"}
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

async def validate_file(file: UploadFile):
    """Checks file type and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (FastAPI SpooledTemporaryFile might not have size until read)
    # Read a chunk to check size safely
    contents = await file.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Reset file pointer for subsequent reads
    await file.seek(0)
    return True

async def verify_recaptcha(recaptcha_token: Optional[str] = Form(None)):
    """Verifies reCAPTCHA token with Google (only in production)."""
    if not IS_PRODUCTION:
        return True
    
    if not recaptcha_token:
        logger.error("Production reCAPTCHA check failed: Token missing.")
        raise HTTPException(
            status_code=400, 
            detail="reCAPTCHA verification required for security."
        )
    
    if not RECAPTCHA_SECRET_KEY:
        logger.error("Production reCAPTCHA check failed: SECRET_KEY not configured.")
        raise HTTPException(
            status_code=500, 
            detail="reCAPTCHA service misconfigured in production."
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": recaptcha_token,
            },
        )
        result = response.json()
        
        if not result.get("success"):
            logger.warning(f"reCAPTCHA failed for token: {recaptcha_token[:10]}... Error: {result.get('error-codes')}")
            raise HTTPException(
                status_code=403, 
                detail="reCAPTCHA verification failed. Please try again."
            )
    
    return True
