import os
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from starlette.requests import ClientDisconnect
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

async def verify_github_signature(request: Request):
    """
    Verifies that the incoming request is actually from GitHub.
    Uses HMAC SHA-256 and constant-time comparison.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Missing X-Hub-Signature-256 header"
        )
    
    # Get the raw body bytes (critical: do not parse as JSON yet)
    try:
        payload_body = await request.body()
    except ClientDisconnect:
        # GitHub closed connection early - this happens occasionally
        # Log it but don't crash the server
        print("⚠️ Webhook: Client disconnected before body was read")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client disconnected"
        )
    
    if not WEBHOOK_SECRET:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Server Misconfiguration: GITHUB_WEBHOOK_SECRET not set"
        )

    # Calculate the expected hash
    hash_object = hmac.new(
        key=WEBHOOK_SECRET.encode("utf-8"), 
        msg=payload_body, 
        digestmod=hashlib.sha256
    )
    expected_signature = f"sha256={hash_object.hexdigest()}"
    
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid signature. You are not GitHub."
        )
        
    return True