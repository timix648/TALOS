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
    
    Uses an asyncio.Queue bridge with a background reader task so we can
    send SSE keep-alive comments (`: keepalive`) every 15 seconds when
    no events arrive.  This prevents proxies and browsers from closing
    idle connections during long-running phases like Visual Cortex capture.
    
    SSE Format:
        event: <event_type>
        data: <json_payload>
        
        (blank line to separate events)
    """
    bus = await get_event_bus()
 
    history = await bus.get_history(run_id)
    is_already_complete = False
    
    for event in history:
        yield f"event: {event.event_type.value}\ndata: {event.to_json()}\n\n"

        if event.event_type in (EventType.MISSION_END, EventType.SUCCESS, EventType.FAILURE):
            is_already_complete = True
    
  
    yield f"event: connected\ndata: {{\"run_id\": \"{run_id}\", \"message\": \"Connected to TALOS Neural Stream\"}}\n\n"
    
 
    if is_already_complete:
        yield f"event: complete\ndata: {{\"message\": \"Run already completed\"}}\n\n"
        return
 
    queue: asyncio.Queue = asyncio.Queue()

    async def _reader():
        """Background task that pumps events from Redis into the queue."""
        try:
            async for event in bus.subscribe(run_id):
                await queue.put(event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"SSE reader error for {run_id}: {e}")
     
        await queue.put(None)

    reader_task = asyncio.create_task(_reader())

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
               
                yield ": keepalive\n\n"
                continue

            if event is None:
          
                break

            yield f"event: {event.event_type.value}\ndata: {event.to_json()}\n\n"

    except asyncio.CancelledError:
      
        yield f"event: disconnected\ndata: {{\"message\": \"Stream ended\"}}\n\n"
    finally:
        reader_task.cancel()
        try:
            await reader_task
        except asyncio.CancelledError:
            pass


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
            "X-Accel-Buffering": "no",  
            "Access-Control-Allow-Origin": "*",
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
        print(f"Failed to get history for {run_id}: {e}")
       
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
