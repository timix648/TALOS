import time
import jwt
import os
import logging
import httpx
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

logger = logging.getLogger("autonode.auth")
logging.basicConfig(level=logging.INFO)

load_dotenv()

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

_CLOCK_SKEW_OFFSET = None

def get_clock_skew_offset() -> int:
    """
    Calculates the time difference between Local System (2026) and GitHub (2025).
    """
    global _CLOCK_SKEW_OFFSET
    if _CLOCK_SKEW_OFFSET is not None:
        return _CLOCK_SKEW_OFFSET

    try:
      
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("https://api.github.com")
            
        server_date_str = resp.headers.get("Date")
        if not server_date_str:
            return 0

       
        server_dt = parsedate_to_datetime(server_date_str)
        server_ts = server_dt.timestamp()
        local_ts = time.time()

        _CLOCK_SKEW_OFFSET = int(server_ts - local_ts)
        
    
        logger.info(f"Time Sync: Local={int(local_ts)}, GitHub={int(server_ts)}")
        logger.info(f"Applied Offset: {_CLOCK_SKEW_OFFSET} seconds")
        
        return _CLOCK_SKEW_OFFSET
    except Exception as e:
        logger.warning(f"Could not sync time with GitHub: {e}")
        return 0

def load_private_key() -> bytes:
    if not GITHUB_PRIVATE_KEY_PATH:
        raise ValueError("GITHUB_PRIVATE_KEY_PATH is not set.")

    clean_path = GITHUB_PRIVATE_KEY_PATH.strip().strip('"').strip("'")
    key_data = b""
    
    if os.path.exists(clean_path):
        logger.info(f"Loading private key from file: {clean_path}")
        with open(clean_path, 'rb') as f:
            key_data = f.read()
        logger.info(f"   Key size: {len(key_data)} bytes")
    else:
        logger.warning(f"Key file not found at: {clean_path}")
        logger.warning("   Attempting to use path as raw key content...")
        key_data = GITHUB_PRIVATE_KEY_PATH.encode('utf-8')

  
    if b"\\n" in key_data:
        logger.info("   Converting escaped newlines...")
        key_data = key_data.decode('utf-8').replace("\\n", "\n").encode('utf-8')

  
    if not key_data.startswith(b"-----BEGIN"):
        logger.error("INVALID KEY: Does not start with -----BEGIN")
        raise ValueError("Private key has invalid format - must start with -----BEGIN")
    
    if b"-----END" not in key_data:
        logger.error("INVALID KEY: Missing -----END marker")
        raise ValueError("Private key has invalid format - missing -----END marker")

    return key_data

def generate_jwt() -> str:
    if not GITHUB_APP_ID:
        raise ValueError("GITHUB_APP_ID is missing.")

    private_key = load_private_key()

    logger.debug(f"Key starts with: {private_key[:50]}")

    offset = get_clock_skew_offset()
    
    
    now_github_time = int(time.time() + offset)

    app_id_str = str(GITHUB_APP_ID).strip()
    
    payload = {
        "iat": now_github_time - 60,  
        "exp": now_github_time + (9 * 60),  
        "iss": app_id_str
    }
    
    logger.info(f"JWT Payload: iat={payload['iat']}, exp={payload['exp']}, iss={payload['iss']}")

    return jwt.encode(payload, private_key, algorithm="RS256")

async def get_installation_access_token(installation_id: int) -> str:
    jwt_token = generate_jwt()
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    logger.info(f"Requesting access token for installation: {installation_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens", 
                headers=headers
            )
            
            logger.info(f"GitHub Response: {resp.status_code}")
            
            if resp.status_code == 401:
                error_body = resp.text
                logger.critical(f"Auth Failed (401). Response: {error_body}")
                raise Exception(f"GitHub Authentication Failed: 401 Unauthorized - {error_body}")
                
            if resp.status_code != 201:
                error_body = resp.text
                logger.error(f"Auth Failed ({resp.status_code}). Response: {error_body}")
                raise Exception(f"Failed to get access token: {resp.status_code} - {error_body}")
                
            return resp.json()["token"]
    except httpx.TimeoutException:
        logger.error("GitHub API timeout - request took too long")
        raise Exception("GitHub API request timed out after 30 seconds")
    except httpx.ConnectError as e:
        logger.error(f"Connection error to GitHub: {e}")
        raise Exception(f"Cannot connect to GitHub API: {e}")
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            raise  
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        raise