from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.security import verify_github_signature
from app.db.supabase import save_installation
from app.core.agent import run_healing_mission
from app.routes.events import router as events_router
from app.routes.runs import router as runs_router
from app.routes.installations import router as installations_router
from app.routes.stats import router as stats_router
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(
    title="TALOS Neural System",
    description="The Self-Healing DevOps Species - Autonomous CI/CD Repair",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(events_router)
app.include_router(runs_router)
app.include_router(installations_router)
app.include_router(stats_router)

@app.get("/")
def health_check():
    return {
        "status": "alive", 
        "system": "TALOS v1.0",
        "species": "Self-Healing DevOps Agent",
        "capabilities": ["syntax_repair", "logic_debugging", "visual_regression", "pr_creation"]
    }

@app.post("/webhook", dependencies=[Depends(verify_github_signature)])
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives the webhook and dispatches the Agent in the background.
    Returns immediately with a run_id for SSE subscription.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")
    
    print(f"📨 Signal Received: {event_type}")

    # --- NEW: HANDLE INSTALLATION EVENTS ---
    if event_type == "installation":
        action = payload.get("action")
        # Handle new installs, permissions updates, or unsuspensions
        if action in ["created", "new_permissions_accepted", "unsuspend"]:
            install = payload.get("installation", {})
            account = install.get("account", {})
            
            print(f"💾 Saving Installation: {install.get('id')} for {account.get('login')}")
            
            await save_installation(
                github_installation_id=install.get("id"),
                account_login=account.get("login"),
                account_type=account.get("type")
            )
            return {"status": "installation_saved"}
            
        if action == "deleted":
            print(f"🗑️ Installation deleted: {payload.get('installation', {}).get('id')}")
            return {"status": "installation_deleted"}
    # ----------------------------------------

    if event_type == "workflow_run":
        action = payload.get("action")
        conclusion = payload.get("workflow_run", {}).get("conclusion")
        
        # Trigger on FAILURE
        if action == "completed" and conclusion == "failure":
            # Generate unique run ID for tracking
            run_id = str(uuid.uuid4())[:8]
            repo_name = payload.get("repository", {}).get("full_name", "unknown")
            
            print(f"🚨 PAIN SIGNAL: Build Failed in {repo_name}!")
            print(f"🎫 Run ID: {run_id} - Subscribe at /events/stream/{run_id}")
            
            # Pass run_id to agent for event broadcasting
            background_tasks.add_task(run_healing_mission, payload, run_id)
            
            return {
                "status": "healing_initiated",
                "run_id": run_id,
                "stream_url": f"/events/stream/{run_id}",
                "message": f"TALOS is healing {repo_name}"
            }

    # Also Trigger on PING (When you install the app)
    if event_type == "ping":
        print("✨ TALOS: Installation Ping received!")
        return {"status": "connected", "message": "TALOS is watching"}

    return {"status": "ignored"}


@app.get("/debug/auth")
async def debug_auth():
    """
    Debug endpoint to test GitHub App authentication.
    """
    from app.core.github_auth import generate_jwt, load_private_key
    import httpx
    
    try:
        # Try loading the key
        key = load_private_key()
        key_info = f"Key loaded: {len(key)} bytes, starts with {key[:30].decode('utf-8', errors='ignore')}..."
        
        # Generate JWT
        token = generate_jwt()
        jwt_info = f"JWT generated: {len(token)} chars"
        
        # Test with GitHub API
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.github.com/app", headers=headers)
            
            if resp.status_code == 200:
                app_info = resp.json()
                return {
                    "status": "success",
                    "key_info": key_info,
                    "jwt_info": jwt_info,
                    "app_name": app_info.get("name"),
                    "app_id": app_info.get("id"),
                    "app_url": app_info.get("html_url"),
                    "message": "✅ GitHub App authentication is working!"
                }
            else:
                return {
                    "status": "auth_failed",
                    "key_info": key_info,
                    "jwt_info": jwt_info,
                    "github_status": resp.status_code,
                    "github_response": resp.text,
                    "message": "❌ GitHub rejected the JWT - private key likely doesn't match the registered public key"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "❌ Failed to authenticate with GitHub"
        }