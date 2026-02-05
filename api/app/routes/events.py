"""
SSE EVENTS ENDPOINT: The Neural Stream
=======================================
This endpoint allows frontends to subscribe to real-time updates
from healing runs via Server-Sent Events (SSE).

The "Glass Box" experience - users watch the agent think in real-time.
This is what makes TALOS stand out from 300+ black-box competitors.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio

from app.core.event_bus import get_event_bus, HealingEvent, EventType

router = APIRouter(prefix="/events", tags=["Real-Time Events"])


async def event_generator(run_id: str) -> AsyncGenerator[str, None]:
    """
    Generates SSE-formatted events for a healing run.
    
    SSE Format:
        event: <event_type>
        data: <json_payload>
        
        (blank line to separate events)
    """
    bus = await get_event_bus()
    
    # First, send any historical events (for late-joiners)
    history = await bus.get_history(run_id)
    is_already_complete = False
    
    for event in history:
        yield f"event: {event.event_type.value}\ndata: {event.to_json()}\n\n"
        # Check if run already completed
        if event.event_type in (EventType.MISSION_END, EventType.SUCCESS, EventType.FAILURE):
            is_already_complete = True
    
    # Send a "connected" ping
    yield f"event: connected\ndata: {{\"run_id\": \"{run_id}\", \"message\": \"Connected to TALOS Neural Stream\"}}\n\n"
    
    # If run already completed, don't wait for more events
    if is_already_complete:
        yield f"event: complete\ndata: {{\"message\": \"Run already completed\"}}\n\n"
        return
    
    # Now stream live events
    try:
        async for event in bus.subscribe(run_id):
            yield f"event: {event.event_type.value}\ndata: {event.to_json()}\n\n"
            
            # Keep-alive ping every event
            await asyncio.sleep(0.01)
            
    except asyncio.CancelledError:
        # Client disconnected
        yield f"event: disconnected\ndata: {{\"message\": \"Stream ended\"}}\n\n"


@router.get("/stream/{run_id}")
async def stream_healing_events(run_id: str):
    """
    Subscribe to real-time events for a healing run.
    
    This endpoint uses Server-Sent Events (SSE) to stream
    the agent's thoughts, actions, and results to the frontend.
    
    Usage (JavaScript):
        const eventSource = new EventSource('/events/stream/abc123');
        
        eventSource.addEventListener('thinking', (e) => {
            const data = JSON.parse(e.data);
            console.log('Agent thinking:', data.description);
        });
        
        eventSource.addEventListener('success', (e) => {
            console.log('Healing complete!');
            eventSource.close();
        });
    """
    return StreamingResponse(
        event_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for frontend
        }
    )


@router.get("/history/{run_id}")
async def get_run_history(run_id: str):
    """
    Get the event history for a healing run.
    Useful for loading past events when opening the dashboard.
    """
    try:
        bus = await get_event_bus()
        history = await bus.get_history(run_id)
        
        return {
            "run_id": run_id,
            "events": [
                {
                    "event_type": e.event_type.value,
                    "title": e.title,
                    "description": e.description,
                    "timestamp": e.timestamp,
                    "metadata": e.metadata
                }
                for e in history
            ]
        }
    except Exception as e:
        print(f"❌ Failed to get history for {run_id}: {e}")
        # Return empty events on error so frontend doesn't crash
        return {
            "run_id": run_id,
            "events": [],
            "error": str(e)
        }


@router.get("/health")
async def events_health():
    """Check if the event bus is healthy."""
    try:
        bus = await get_event_bus()
        await bus.connect()
        return {"status": "healthy", "message": "Event bus connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Event bus unhealthy: {e}")
