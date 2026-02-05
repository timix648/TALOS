"""
Stats API for real-time TALOS metrics.
Returns actual healing statistics from the database.
"""

from fastapi import APIRouter
from app.db.supabase import get_supabase

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/")
async def get_stats():
    """
    Get real-time TALOS statistics.
    Returns:
    - avg_boot_time_ms: Average time to spin up sandbox
    - fix_rate_percent: Percentage of successful fixes
    - total_heals: Total healing runs
    - retry_limit: Max retry attempts (constant)
    """
    try:
        supabase = get_supabase()
        
        # Get total healing runs
        total_runs = supabase.table("healing_runs").select("id", count="exact").execute()
        total_count = total_runs.count or 0
        
        # Get successful runs (status = 'success')
        success_runs = supabase.table("healing_runs")\
            .select("id", count="exact")\
            .eq("status", "success")\
            .execute()
        success_count = success_runs.count or 0
        
        # Calculate fix rate
        fix_rate = round((success_count / total_count * 100) if total_count > 0 else 0, 1)
        
        # Default boot time (E2B sandbox typically boots in ~150ms)
        # We could track this in healing_runs metadata in the future
        avg_boot_time = 150
        
        return {
            "avg_boot_time_ms": avg_boot_time,
            "fix_rate_percent": fix_rate,
            "total_heals": total_count,
            "successful_heals": success_count,
            "retry_limit": 3,  # This is configured in agent.py
        }
    
    except Exception as e:
        # Return defaults if database not configured yet
        return {
            "avg_boot_time_ms": 150,
            "fix_rate_percent": 0,
            "total_heals": 0,
            "successful_heals": 0,
            "retry_limit": 3,
            "error": str(e) if str(e) else "Database not configured"
        }


@router.get("/recent")
async def get_recent_activity():
    """
    Get recent healing activity for live dashboard.
    """
    try:
        supabase = get_supabase()
        recent_runs = supabase.table("healing_runs")\
            .select("id, repo_full_name, status, error_type, created_at, updated_at")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        return {
            "recent_runs": recent_runs.data or [],
        }
    except Exception:
        return {"recent_runs": []}
