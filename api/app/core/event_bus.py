"""
EVENT BUS: The Neural Broadcast System
=======================================
This module implements a Redis-backed pub/sub system that allows the agent
to broadcast its "thoughts" in real-time to connected frontends via SSE.

This is THE differentiator - while other agents are black boxes,
TALOS shows its reasoning process live, building trust and engagement.

Architecture:
  Agent (Publisher) → Redis Channel → SSE Endpoint → Frontend Timeline
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class EventType(str, Enum):
  
    MISSION_START = "mission_start"      
    MISSION_END = "mission_end"         
    
    CLONING = "cloning"                 
    SCOUTING = "scouting"               
    READING_CODE = "reading_code"        
    
    
    THINKING = "thinking"                
    ANALYZING = "analyzing"             
    DIAGNOSING = "diagnosing"           
    
    APPLYING_FIX = "applying_fix"      
    VERIFYING = "verifying"             
    CREATING_PR = "creating_pr"         
    
    
    SUCCESS = "success"                 
    FAILURE = "failure"                 
    RETRY = "retry"                     
    
    
    CODE_DIFF = "code_diff"             
    ERROR_LOG = "error_log"            
    THOUGHT_STREAM = "thought_stream"   
    
  
    SCREENSHOT = "screenshot"          
    VISUAL_ANALYSIS = "visual_analysis"  


@dataclass
class HealingEvent:
    """A single event in the healing timeline."""
    run_id: str
    event_type: EventType
    title: str
    description: str
    timestamp: str = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_json(self) -> str:
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "HealingEvent":
        data = json.loads(json_str)
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)


class EventBus:
    """
    Redis-backed event bus for real-time agent communication.
    
    Usage:
        # Publishing (from agent)
        bus = EventBus()
        await bus.publish(HealingEvent(
            run_id="abc123",
            event_type=EventType.THINKING,
            title="Analyzing Error",
            description="The error appears to be a SyntaxError in line 42..."
        ))
        
        # Subscribing (from SSE endpoint)
        async for event in bus.subscribe("abc123"):
            yield f"data: {event.to_json()}\n\n"
    """
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
    
    async def connect(self):
        """Establish Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                await self._redis.ping()
                print(f"Redis connected: {REDIS_URL}")
            except Exception as e:
                print(f"Redis connection failed: {e}")
                raise
    
    async def disconnect(self):
        """Clean up Redis connection."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
    
    def _channel_name(self, run_id: str) -> str:
        """Generate channel name for a healing run."""
        return f"talos:healing:{run_id}"
    
    async def publish(self, event: HealingEvent):
        """Publish an event to the healing run's channel."""
        try:
            await self.connect()
            channel = self._channel_name(event.run_id)
            await self._redis.publish(channel, event.to_json())
            
          
            history_key = f"talos:history:{event.run_id}"
            await self._redis.rpush(history_key, event.to_json())
            await self._redis.ltrim(history_key, -100, -1) 
            await self._redis.expire(history_key, 3600)  
            
            print(f"Event published: {event.event_type.value} - {event.title}")
        except Exception as e:
            print(f"Failed to publish event: {e}")
        
        try:
            persist_metadata = event.metadata
            if persist_metadata and "screenshot_base64" in persist_metadata:
                persist_metadata = {k: v for k, v in persist_metadata.items() if k != "screenshot_base64"}
                persist_metadata["has_screenshot"] = True
            
            from app.db.supabase import persist_healing_event
            await persist_healing_event(
                run_id=event.run_id,
                event_type=event.event_type.value,
                title=event.title,
                description=event.description,
                metadata=persist_metadata,
            )
        except Exception as e:
           
            pass
    
    async def get_history(self, run_id: str) -> list[HealingEvent]:
        """Get historical events for a run (for late-joining clients)."""
        await self.connect()
        history_key = f"talos:history:{run_id}"
        events_json = await self._redis.lrange(history_key, 0, -1)
        return [HealingEvent.from_json(e) for e in events_json]
    
    async def subscribe(self, run_id: str) -> AsyncGenerator[HealingEvent, None]:
        """
        Subscribe to events for a specific healing run.
        Yields events as they arrive.
        """
        await self.connect()
        channel = self._channel_name(run_id)
        
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    event = HealingEvent.from_json(message["data"])
                    yield event
                    
                    
                    if event.event_type in (EventType.MISSION_END, EventType.SUCCESS, EventType.FAILURE):
                        break
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()



_event_bus: Optional[EventBus] = None

async def get_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.connect()
    return _event_bus

async def emit(
    run_id: str,
    event_type: EventType,
    title: str,
    description: str = "",
    metadata: dict = None
):
    """
    Quick helper to emit an event from anywhere in the agent code.
    
    Usage:
        await emit(run_id, EventType.THINKING, "Analyzing Error", "Found SyntaxError...")
    """
    bus = await get_event_bus()
    event = HealingEvent(
        run_id=run_id,
        event_type=event_type,
        title=title,
        description=description,
        metadata=metadata
    )
    await bus.publish(event)


async def emit_thought(run_id: str, thought: str):
    """Emit a thought from the agent's reasoning process."""
    await emit(run_id, EventType.THOUGHT_STREAM, "Thinking", thought)


async def emit_code_diff(run_id: str, filepath: str, before: str, after: str):
    """Emit a code diff for visualization."""
    await emit(
        run_id, 
        EventType.CODE_DIFF, 
        f"Proposed Fix: {filepath}",
        "",
        metadata={"filepath": filepath, "before": before, "after": after}
    )


async def emit_screenshot(run_id: str, title: str, screenshot_base64: str, description: str = ""):
    """Emit a screenshot for the Visual Cortex display."""
    await emit(
        run_id,
        EventType.SCREENSHOT,
        f"{title}",
        description,
        metadata={"screenshot_base64": screenshot_base64}
    )


async def emit_visual_analysis(run_id: str, analysis: dict):
    """Emit visual analysis results from Gemini Vision."""
    has_issues = analysis.get("has_issues", False)
    issues_count = len(analysis.get("issues", []))
    title = f"{issues_count} Visual Issue(s) Detected" if has_issues else "No Visual Issues"
    await emit(
        run_id,
        EventType.VISUAL_ANALYSIS,
        title,
        analysis.get("screenshot_description", ""),
        metadata=analysis
    )
