import hmac
import hashlib
import json
import os
import httpx # Changed from requests to httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
TARGET_URL = "http://localhost:8000/webhook"
SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# 1. The Mock Payload
payload = {
    "action": "completed",
    "workflow_run": {
        "id": 106691814,
        "name": "CI/CD",
        "head_branch": "feature/broken-button",
        "conclusion": "failure" 
    },
    "installation": {
        "id": 106691814 
    },
    "repository": {
        "full_name": "timix648/A-self-healing-pipeline",
        "clone_url": "https://github.com/timix648/A-self-healing-pipeline"
    }
}

async def send_trigger():
    payload_bytes = json.dumps(payload).encode('utf-8')

    # 2. Sign the payload
    if not SECRET:
        print("❌ Error: GITHUB_WEBHOOK_SECRET is missing in .env")
        exit(1)

    hash_object = hmac.new(
        key=SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    )
    signature = f"sha256={hash_object.hexdigest()}"

    # 3. Send the signal
    print(f"📨 Sending Mock Webhook to {TARGET_URL}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TARGET_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "workflow_run",
                    "X-Hub-Signature-256": signature
                },
                content=payload_bytes
            )
            print(f"✅ Response: {response.status_code}")
            print(f"📄 Body: {response.json()}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Make sure the server is running on port 8000!")

if __name__ == "__main__":
    asyncio.run(send_trigger())