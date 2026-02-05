"""
INSTALLATIONS ROUTE
====================
Handles GitHub App installation management.
Syncs installations from the OAuth flow to Supabase.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase import save_installation, get_installation

router = APIRouter(prefix="/installations", tags=["Installations"])


class InstallationCreate(BaseModel):
    github_installation_id: int
    account_login: str
    account_type: str = "User"
    access_token: Optional[str] = None


class InstallationResponse(BaseModel):
    id: str
    github_installation_id: int
    account_login: str
    account_type: str
    created_at: str


@router.post("", response_model=InstallationResponse)
async def create_or_update_installation(data: InstallationCreate):
    """
    Create or update a GitHub App installation.
    Called from the frontend after OAuth callback.
    """
    try:
        result = await save_installation(
            github_installation_id=data.github_installation_id,
            account_login=data.account_login,
            account_type=data.account_type
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save installation")
        
        return result
        
    except Exception as e:
        print(f"❌ Installation save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{installation_id}/sync")
async def sync_installation(installation_id: int):
    """
    Sync an installation - fetches repos and updates database.
    Called after app installation to discover accessible repos.
    """
    from app.core.github_auth import get_installation_access_token
    import httpx
    
    try:
        # Get access token for this installation
        token = await get_installation_access_token(installation_id)
        
        # Fetch accessible repositories
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/installation/repositories",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch repos")
            
            data = response.json()
            repos = data.get("repositories", [])
            
            print(f"📦 Found {len(repos)} accessible repositories for installation {installation_id}")
            
            return {
                "installation_id": installation_id,
                "repositories": [
                    {
                        "full_name": r["full_name"],
                        "private": r["private"],
                        "default_branch": r.get("default_branch", "main"),
                    }
                    for r in repos
                ],
                "total_count": len(repos),
            }
            
    except Exception as e:
        print(f"❌ Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{installation_id}")
async def get_installation_details(installation_id: int):
    """
    Get details for a specific installation.
    """
    try:
        result = await get_installation(installation_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{installation_id}/repos")
async def list_installation_repos(installation_id: int):
    """
    List all repositories accessible to an installation.
    """
    from app.core.github_auth import get_installation_access_token
    from app.db.supabase import get_supabase
    import httpx
    
    try:
        token = await get_installation_access_token(installation_id)
        supabase = get_supabase()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/installation/repositories",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                }
            )
            
            data = response.json()
            github_repos = data.get("repositories", [])
            
            # Get watched status from our database
            watched = supabase.table("watched_repos")\
                .select("repo_full_name, auto_heal_enabled, safe_mode")\
                .execute()
            
            watched_map = {r["repo_full_name"]: r for r in (watched.data or [])}
            
            # Merge GitHub repos with our watch status
            repos_with_status = []
            for repo in github_repos:
                full_name = repo["full_name"]
                watch_info = watched_map.get(full_name, {})
                repos_with_status.append({
                    "full_name": full_name,
                    "name": repo["name"],
                    "private": repo["private"],
                    "default_branch": repo.get("default_branch", "main"),
                    "description": repo.get("description"),
                    "watched": full_name in watched_map,
                    "auto_heal_enabled": watch_info.get("auto_heal_enabled", False),
                    "safe_mode": watch_info.get("safe_mode", True),
                })
            
            return {
                "repositories": repos_with_status,
                "total_count": len(repos_with_status),
            }
            
    except Exception as e:
        print(f"❌ REPO LIST ERROR: {e}")  # <--- THIS IS THE CRITICAL LINE
        raise HTTPException(status_code=500, detail=str(e))
    
    """
    List all repositories accessible to an installation.
    """
    from app.core.github_auth import get_installation_access_token
    from app.db.supabase import get_supabase
    import httpx
    
    try:
        token = await get_installation_access_token(installation_id)
        supabase = get_supabase()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/installation/repositories",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                }
            )
            
            data = response.json()
            github_repos = data.get("repositories", [])
            
            # Get watched status from our database
            watched = supabase.table("watched_repos")\
                .select("repo_full_name, auto_heal_enabled, safe_mode")\
                .execute()
            
            watched_map = {r["repo_full_name"]: r for r in (watched.data or [])}
            
            # Merge GitHub repos with our watch status
            repos_with_status = []
            for repo in github_repos:
                full_name = repo["full_name"]
                watch_info = watched_map.get(full_name, {})
                repos_with_status.append({
                    "full_name": full_name,
                    "name": repo["name"],
                    "private": repo["private"],
                    "default_branch": repo.get("default_branch", "main"),
                    "description": repo.get("description"),
                    "watched": full_name in watched_map,
                    "auto_heal_enabled": watch_info.get("auto_heal_enabled", False),
                    "safe_mode": watch_info.get("safe_mode", True),
                })
            
            return {
                "repositories": repos_with_status,
                "total_count": len(repos_with_status),
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class WatchRepoRequest(BaseModel):
    repo_full_name: str
    auto_heal_enabled: bool = True
    safe_mode: bool = True


@router.post("/{installation_id}/watch")
async def watch_repo(installation_id: int, data: WatchRepoRequest):
    """
    Start watching a repository for CI failures.
    """
    from app.db.supabase import get_supabase
    
    try:
        supabase = get_supabase()
        # Get our internal installation ID
        inst = supabase.table("installations")\
            .select("id")\
            .eq("github_installation_id", installation_id)\
            .single()\
            .execute()
        
        if not inst.data:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        # Upsert the watched repo
        result = supabase.table("watched_repos").upsert({
            "installation_id": inst.data["id"],
            "repo_full_name": data.repo_full_name,
            "auto_heal_enabled": data.auto_heal_enabled,
            "safe_mode": data.safe_mode,
        }, on_conflict="installation_id,repo_full_name").execute()
        
        print(f"👁️ Now watching: {data.repo_full_name}")
        
        return {
            "success": True,
            "repo": data.repo_full_name,
            "watching": True,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{installation_id}/watch/{repo_owner}/{repo_name}")
async def unwatch_repo(installation_id: int, repo_owner: str, repo_name: str):
    """
    Stop watching a repository.
    """
    from app.db.supabase import get_supabase
    
    repo_full_name = f"{repo_owner}/{repo_name}"
    
    try:
        supabase = get_supabase()
        # Get our internal installation ID
        inst = supabase.table("installations")\
            .select("id")\
            .eq("github_installation_id", installation_id)\
            .single()\
            .execute()
        
        if not inst.data:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        # Delete the watch
        supabase.table("watched_repos")\
            .delete()\
            .eq("installation_id", inst.data["id"])\
            .eq("repo_full_name", repo_full_name)\
            .execute()
        
        print(f"🚫 Stopped watching: {repo_full_name}")
        
        return {
            "success": True,
            "repo": repo_full_name,
            "watching": False,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
