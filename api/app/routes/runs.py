"""
RUNS API: Healing Run Management Endpoints
===========================================
REST endpoints for querying and managing healing runs.
Used by the Neural Dashboard to display run history.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.db.supabase import (
    get_recent_runs, 
    get_healing_run, 
    get_run_stats,
    delete_healing_run,
    HealingRun as DBHealingRun
)

router = APIRouter(prefix="/runs", tags=["Healing Runs"])


# Response models
class RunResponse(BaseModel):
    id: Optional[str]
    run_id: str
    repo_full_name: str
    status: str
    error_type: Optional[str]
    patient_zero: Optional[str]
    pr_url: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class RunStatsResponse(BaseModel):
    total: int
    success: int
    failure: int
    running: int
    success_rate: float


class RunListResponse(BaseModel):
    runs: List[RunResponse]
    total: int


@router.get("/", response_model=RunListResponse)
async def list_runs(
    repo: Optional[str] = Query(None, description="Filter by repository"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of runs to return")
):
    """
    List recent healing runs with optional filters.
    """
    try:
        runs = await get_recent_runs(
            repo_full_name=repo,
            status=status,
            limit=limit
        )
        
        return RunListResponse(
            runs=[
                RunResponse(
                    id=r.id,
                    run_id=r.run_id,
                    repo_full_name=r.repo_full_name,
                    status=r.status,
                    error_type=r.error_type,
                    patient_zero=r.patient_zero,
                    pr_url=r.pr_url,
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                )
                for r in runs
            ],
            total=len(runs)
        )
    except Exception as e:
        # If Supabase isn't configured, return empty list
        return RunListResponse(runs=[], total=0)


@router.get("/stats", response_model=RunStatsResponse)
async def get_stats(
    installation_id: Optional[str] = Query(None, description="Filter by installation")
):
    """
    Get aggregate statistics for healing runs.
    """
    try:
        stats = await get_run_stats(installation_id)
        return RunStatsResponse(**stats)
    except Exception:
        return RunStatsResponse(total=0, success=0, failure=0, running=0, success_rate=0)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    """
    Get details for a specific healing run.
    """
    try:
        run = await get_healing_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return RunResponse(
            id=run.id,
            run_id=run.run_id,
            repo_full_name=run.repo_full_name,
            status=run.status,
            error_type=run.error_type,
            patient_zero=run.patient_zero,
            pr_url=run.pr_url,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/active")
async def get_latest_active():
    """
    Get the most recently started active run.
    Used by dashboard to auto-subscribe to SSE.
    """
    try:
        runs = await get_recent_runs(status="running", limit=1)
        if runs:
            run = runs[0]
            return {
                "run_id": run.run_id,
                "repo": run.repo_full_name,
                "started_at": run.started_at,
                "stream_url": f"/events/stream/{run.run_id}"
            }
        return {"run_id": None, "message": "No active runs"}
    except Exception:
        return {"run_id": None, "message": "Database not configured"}


@router.delete("/{run_id}")
async def remove_run(run_id: str):
    """
    Delete a healing run from the database.
    Useful for cleaning up test runs or failed entries.
    """
    try:
        run = await get_healing_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        success = await delete_healing_run(run_id)
        if success:
            return {"success": True, "message": f"Run {run_id} deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete run")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/allow-retry")
async def allow_retry(run_id: str):
    """
    Allow TALOS to push another fix for a repo, bypassing the duplicate PR check.
    
    This sets a flag that the agent checks before skipping PR creation.
    """
    try:
        run = await get_healing_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Store the retry permission in memory (simple approach)
        # The agent will check this before skipping
        from app.core.agent import RETRY_ALLOWED_REPOS
        RETRY_ALLOWED_REPOS.add(run.repo_full_name)
        
        return {
            "success": True,
            "repo": run.repo_full_name,
            "message": f"TALOS can now push another fix to {run.repo_full_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
