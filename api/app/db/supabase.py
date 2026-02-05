"""
SUPABASE PERSISTENCE LAYER
===========================
This module provides database operations for TALOS using Supabase.
Stores installation data, watched repos, and healing run history.

Schema (create in Supabase):

-- Installations table
CREATE TABLE installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_installation_id BIGINT UNIQUE NOT NULL,
    account_login TEXT NOT NULL,
    account_type TEXT DEFAULT 'User',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watched repos table  
CREATE TABLE watched_repos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID REFERENCES installations(id) ON DELETE CASCADE,
    repo_full_name TEXT NOT NULL,
    auto_heal_enabled BOOLEAN DEFAULT TRUE,
    safe_mode BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(installation_id, repo_full_name)
);

-- Healing runs table
CREATE TABLE healing_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT UNIQUE NOT NULL,
    installation_id UUID REFERENCES installations(id),
    repo_full_name TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    error_type TEXT,
    patient_zero TEXT,
    pr_url TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_runs_status ON healing_runs(status);
CREATE INDEX idx_runs_repo ON healing_runs(repo_full_name);
CREATE INDEX idx_runs_started ON healing_runs(started_at DESC);
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # Use service role key for backend

# Lazy initialization
_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create Supabase client."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Installation:
    github_installation_id: int
    account_login: str
    account_type: str = "User"
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class WatchedRepo:
    installation_id: str
    repo_full_name: str
    auto_heal_enabled: bool = True
    safe_mode: bool = True  # True = Create PR, False = Direct commit
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass 
class HealingRun:
    run_id: str
    repo_full_name: str
    installation_id: Optional[str] = None
    status: str = "running"  # running, success, failure
    error_type: Optional[str] = None
    error_message: Optional[str] = None  # Full error message
    patient_zero: Optional[str] = None   # The file that caused the bug
    crash_site: Optional[str] = None     # Where the error manifested
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


# ============================================================================
# INSTALLATION OPERATIONS
# ============================================================================

async def upsert_installation(installation: Installation) -> Installation:
    """Create or update a GitHub App installation."""
    supabase = get_supabase()
    
    data = {
        "github_installation_id": installation.github_installation_id,
        "account_login": installation.account_login,
        "account_type": installation.account_type,
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.table("installations").upsert(
        data, 
        on_conflict="github_installation_id"
    ).execute()
    
    if result.data:
        return Installation(**result.data[0])
    return installation


async def get_installation(github_installation_id: int) -> Optional[Installation]:
    """Get installation by GitHub installation ID."""
    supabase = get_supabase()
    
    try:
        result = supabase.table("installations").select("*").eq(
            "github_installation_id", github_installation_id
        ).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return Installation(**result.data[0])
        return None
    except Exception as e:
        print(f"⚠️ get_installation error: {e}")
        return None


async def delete_installation(github_installation_id: int) -> bool:
    """Delete an installation (cascade deletes watched repos)."""
    supabase = get_supabase()
    
    result = supabase.table("installations").delete().eq(
        "github_installation_id", github_installation_id
    ).execute()
    
    return len(result.data) > 0


# ============================================================================
# WATCHED REPO OPERATIONS
# ============================================================================

async def add_watched_repo(repo: WatchedRepo) -> WatchedRepo:
    """Add a repo to watch list."""
    supabase = get_supabase()
    
    data = asdict(repo)
    data.pop("id", None)  # Let DB generate ID
    
    result = supabase.table("watched_repos").upsert(
        data,
        on_conflict="installation_id,repo_full_name"
    ).execute()
    
    if result.data:
        return WatchedRepo(**result.data[0])
    return repo


async def get_watched_repos(installation_id: str) -> List[WatchedRepo]:
    """Get all watched repos for an installation."""
    supabase = get_supabase()
    
    result = supabase.table("watched_repos").select("*").eq(
        "installation_id", installation_id
    ).execute()
    
    return [WatchedRepo(**r) for r in result.data]


async def update_repo_settings(
    repo_id: str, 
    auto_heal_enabled: Optional[bool] = None,
    safe_mode: Optional[bool] = None
) -> bool:
    """Update repo watching settings."""
    supabase = get_supabase()
    
    data = {}
    if auto_heal_enabled is not None:
        data["auto_heal_enabled"] = auto_heal_enabled
    if safe_mode is not None:
        data["safe_mode"] = safe_mode
    
    if not data:
        return False
    
    result = supabase.table("watched_repos").update(data).eq("id", repo_id).execute()
    return len(result.data) > 0


async def remove_watched_repo(installation_id: str, repo_full_name: str) -> bool:
    """Remove a repo from watch list."""
    supabase = get_supabase()
    
    result = supabase.table("watched_repos").delete().eq(
        "installation_id", installation_id
    ).eq("repo_full_name", repo_full_name).execute()
    
    return len(result.data) > 0


# ============================================================================
# HEALING RUN OPERATIONS
# ============================================================================

async def create_healing_run(run: HealingRun) -> HealingRun:
    """Create a new healing run record."""
    supabase = get_supabase()
    
    data = {
        "run_id": run.run_id,
        "repo_full_name": run.repo_full_name,
        "status": run.status,
        "started_at": run.started_at or datetime.utcnow().isoformat(),
        "metadata": run.metadata or {},
    }
    
    # Only include optional fields if they have values
    if run.installation_id:
        data["installation_id"] = run.installation_id
    if run.error_type:
        data["error_type"] = run.error_type
    if run.patient_zero:
        data["patient_zero"] = run.patient_zero
    
    try:
        result = supabase.table("healing_runs").insert(data).execute()
        
        if result.data:
            print(f"✅ DB: Created healing run {run.run_id}")
            return HealingRun(**result.data[0])
        else:
            print(f"⚠️ DB: No data returned when creating run {run.run_id}")
        return run
    except Exception as e:
        print(f"❌ DB: Failed to create healing run: {e}")
        raise


async def update_healing_run(
    run_id: str,
    status: Optional[str] = None,
    error_type: Optional[str] = None,
    patient_zero: Optional[str] = None,
    pr_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Update a healing run's status and details."""
    supabase = get_supabase()
    
    data = {}
    if status:
        data["status"] = status
        if status in ("success", "failure"):
            data["completed_at"] = datetime.utcnow().isoformat()
    if error_type:
        data["error_type"] = error_type
    if patient_zero:
        data["patient_zero"] = patient_zero
    if pr_url:
        data["pr_url"] = pr_url
    if metadata:
        data["metadata"] = metadata
    
    if not data:
        return False
    
    result = supabase.table("healing_runs").update(data).eq("run_id", run_id).execute()
    return len(result.data) > 0


async def get_healing_run(run_id: str) -> Optional[HealingRun]:
    """Get a healing run by run_id."""
    supabase = get_supabase()
    
    try:
        result = supabase.table("healing_runs").select("*").eq("run_id", run_id).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return HealingRun(**result.data[0])
        return None
    except Exception as e:
        print(f"⚠️ get_healing_run error: {e}")
        return None


async def get_recent_runs(
    repo_full_name: Optional[str] = None,
    installation_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> List[HealingRun]:
    """Get recent healing runs with optional filters."""
    supabase = get_supabase()
    
    query = supabase.table("healing_runs").select("*")
    
    if repo_full_name:
        query = query.eq("repo_full_name", repo_full_name)
    if installation_id:
        query = query.eq("installation_id", installation_id)
    if status:
        query = query.eq("status", status)
    
    result = query.order("started_at", desc=True).limit(limit).execute()
    
    return [HealingRun(**r) for r in result.data]


async def get_run_stats(installation_id: Optional[str] = None) -> Dict[str, Any]:
    """Get aggregate statistics for healing runs."""
    supabase = get_supabase()
    
    query = supabase.table("healing_runs").select("status")
    if installation_id:
        query = query.eq("installation_id", installation_id)
    
    result = query.execute()
    
    stats = {
        "total": len(result.data),
        "success": sum(1 for r in result.data if r["status"] == "success"),
        "failure": sum(1 for r in result.data if r["status"] == "failure"),
        "running": sum(1 for r in result.data if r["status"] == "running"),
    }
    
    stats["success_rate"] = (
        round(stats["success"] / stats["total"] * 100, 1) 
        if stats["total"] > 0 else 0
    )
    
    return stats


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def is_repo_watched(repo_full_name: str) -> bool:
    """Check if a repo is being watched by any installation."""
    supabase = get_supabase()
    
    result = supabase.table("watched_repos").select("id").eq(
        "repo_full_name", repo_full_name
    ).eq("auto_heal_enabled", True).limit(1).execute()
    
    return len(result.data) > 0


async def get_repo_config(repo_full_name: str) -> Optional[WatchedRepo]:
    """Get the configuration for a specific repo."""
    supabase = get_supabase()
    
    result = supabase.table("watched_repos").select("*").eq(
        "repo_full_name", repo_full_name
    ).single().execute()
    
    if result.data:
        return WatchedRepo(**result.data)
    return None

async def delete_healing_run(run_id: str) -> bool:
    """Delete a healing run by run_id."""
    supabase = get_supabase()
    
    try:
        result = supabase.table("healing_runs").delete().eq("run_id", run_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error deleting healing run: {e}")
        return False


# ============================================================================
# ALIAS FUNCTIONS (for route compatibility)
# ============================================================================

def get_supabase_client() -> Client:
    """Alias for get_supabase (for import compatibility)."""
    return get_supabase()


async def save_installation(
    github_installation_id: int,
    account_login: str,
    account_type: str = "User"
) -> Optional[Dict[str, Any]]:
    """
    Save or update a GitHub installation.
    Returns the installation record as a dict.
    """
    installation = Installation(
        github_installation_id=github_installation_id,
        account_login=account_login,
        account_type=account_type
    )
    
    result = await upsert_installation(installation)
    
    if result:
        return {
            "id": result.id,
            "github_installation_id": result.github_installation_id,
            "account_login": result.account_login,
            "account_type": result.account_type,
            "created_at": result.created_at or datetime.utcnow().isoformat(),
        }
    return None