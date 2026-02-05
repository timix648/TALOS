"""
TALOS API Routes
================
"""

from app.routes.events import router as events_router
from app.routes.runs import router as runs_router

__all__ = ["events_router", "runs_router"]
