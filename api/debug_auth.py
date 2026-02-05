import os
import time
import jwt
import httpx
import asyncio
from dotenv import load_dotenv

# Load your .env variables
load_dotenv()

async def test_auth():
    print("\n🕵️ TALOS AUTH DEBUGGER")
    print("=======================")

    # 1. Check Paths
    # Force absolute path resolution like we discussed
    raw_env_path = os.getenv("GITHUB_PRIVATE_KEY_PATH", "talos-private-key.pem")
    if not os.path.isabs(raw_env_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, raw_env_path)
    else:
        key_path = raw_env_path
        
    app_id = os.getenv("GITHUB_APP_ID")
    
    print(f"📂 Key Path Resolved: {key_path}")
    print(f"🆔 App ID: {app_id}")

    # 2. Check File Existence
    if not os.path.exists(key_path):
        print("❌ CRITICAL: File does not exist at this path!")
        return

    # 3. Read Key
    try:
        with open(key_path, 'r') as f:
            private_key = f.read()
        print(f"🔑 Key Loaded: {len(private_key)} chars")
        print(f"   Header: {private_key.splitlines()[0]}")
    except Exception as e:
        print(f"❌ Error reading key: {e}")
        return

    # 4. Generate Token (The Math Part)
    now = int(time.time())
    print(f"⌚ System Time (Unix): {now}")
    
    payload = {
        "iat": now,
        "exp": now + (10 * 60),
        "iss": app_id
    }
    
    try:
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        print("✅ JWT Generated successfully")
    except Exception as e:
        print(f"❌ JWT Generation Failed: {e}")
        return

    # 5. Talk to GitHub (The Test)
    print("\n📡 Connecting to GitHub API...")
    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # We ask "Who am I?"
        response = await client.get("https://api.github.com/app", headers=headers)
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS! Authentication works.")
            print(f"   App Name: {response.json().get('name')}")
            print(f"   App URL:  {response.json().get('html_url')}")
        else:
            print(f"\n💀 FAILURE: GitHub rejected us.")
            print(f"   Status: {response.status_code}")
            print(f"   Reason: {response.text}")
            
            if "expired" in response.text.lower() or "not be decoded" in response.text:
                print("\n💡 HINT: Check your PC's TIME settings. If your clock is wrong, this fails.")

if __name__ == "__main__":
    asyncio.run(test_auth())