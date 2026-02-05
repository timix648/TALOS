import time
import jwt
import os
import logging
import httpx
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

# Initialize Logging
logger = logging.getLogger("autonode.auth")
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Configuration Constants
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

# Global offset cache
_CLOCK_SKEW_OFFSET = None

def get_clock_skew_offset() -> int:
    """
    Calculates the time difference between Local System (2026) and GitHub (2025).
    """
    global _CLOCK_SKEW_OFFSET
    if _CLOCK_SKEW_OFFSET is not None:
        return _CLOCK_SKEW_OFFSET

    try:
        # Ping GitHub to get their server time
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("https://api.github.com")
            
        server_date_str = resp.headers.get("Date")
        if not server_date_str:
            return 0

        # Calculate offset: Server Time - Local Time
        server_dt = parsedate_to_datetime(server_date_str)
        server_ts = server_dt.timestamp()
        local_ts = time.time()

        _CLOCK_SKEW_OFFSET = int(server_ts - local_ts)
        
        # LOG THIS SO WE KNOW IT WORKED
        logger.info(f"⏳ Time Sync: Local={int(local_ts)}, GitHub={int(server_ts)}")
        logger.info(f"⏳ Applied Offset: {_CLOCK_SKEW_OFFSET} seconds")
        
        return _CLOCK_SKEW_OFFSET
    except Exception as e:
        logger.warning(f"⚠️ Could not sync time with GitHub: {e}")
        return 0

def load_private_key() -> bytes:
    if not GITHUB_PRIVATE_KEY_PATH:
        raise ValueError("GITHUB_PRIVATE_KEY_PATH is not set.")

    clean_path = GITHUB_PRIVATE_KEY_PATH.strip().strip('"').strip("'")
    key_data = b""
    
    if os.path.exists(clean_path):
        logger.info(f"✅ Loading private key from file: {clean_path}")
        with open(clean_path, 'rb') as f:
            key_data = f.read()
        logger.info(f"   Key size: {len(key_data)} bytes")
    else:
        logger.warning(f"⚠️ Key file not found at: {clean_path}")
        logger.warning("   Attempting to use path as raw key content...")
        key_data = GITHUB_PRIVATE_KEY_PATH.encode('utf-8')

    # Handle escaped newlines from environment variables
    if b"\\n" in key_data:
        logger.info("   Converting escaped newlines...")
        key_data = key_data.decode('utf-8').replace("\\n", "\n").encode('utf-8')

    # Validate key format
    if not key_data.startswith(b"-----BEGIN"):
        logger.error("❌ INVALID KEY: Does not start with -----BEGIN")
        raise ValueError("Private key has invalid format - must start with -----BEGIN")
    
    if b"-----END" not in key_data:
        logger.error("❌ INVALID KEY: Missing -----END marker")
        raise ValueError("Private key has invalid format - missing -----END marker")

    return key_data

def generate_jwt() -> str:
    if not GITHUB_APP_ID:
        raise ValueError("GITHUB_APP_ID is missing.")

    private_key = load_private_key()
    
    # Log the key header for debugging (first 50 chars only)
    logger.debug(f"🔑 Key starts with: {private_key[:50]}")

    # 1. Get the Time Offset (Fixes the 1-year drift)
    offset = get_clock_skew_offset()
    
    # 2. Calculate "GitHub Time"
    now_github_time = int(time.time() + offset)
    
    # CRITICAL: iss must be a string for GitHub API
    # Some PyJWT versions handle this differently
    app_id_str = str(GITHUB_APP_ID).strip()
    
    payload = {
        "iat": now_github_time - 60,  # Backdate by 60 seconds for clock skew
        "exp": now_github_time + (9 * 60),  # Valid for 9 minutes
        "iss": app_id_str
    }
    
    logger.info(f"🎫 JWT Payload: iat={payload['iat']}, exp={payload['exp']}, iss={payload['iss']}")

    return jwt.encode(payload, private_key, algorithm="RS256")

async def get_installation_access_token(installation_id: int) -> str:
    jwt_token = generate_jwt()
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens", 
            headers=headers
        )
        
        if resp.status_code == 401:
            logger.critical(f"Auth Failed (401). Response: {resp.text}")
            raise Exception("GitHub Authentication Failed: 401 Unauthorized")
            
        if resp.status_code != 201:
            raise Exception(f"Failed to get access token: {resp.status_code}")
            
        return resp.json()["token"]