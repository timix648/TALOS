"""
TALOS AI Chat - Conversational interface for discussing healing runs.
Users can ask questions about any fix, understand the diagnosis, and learn more.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types
from app.core.key_manager import key_rotator
from app.db.supabase import get_supabase

router = APIRouter(prefix="/chat", tags=["chat"])

MODEL_NAME = "gemini-3-flash-preview"  


class ChatMessage(BaseModel):
    role: str  
    content: str


class ChatRequest(BaseModel):
    message: str
    run_id: Optional[str] = None  
    history: list[ChatMessage] = []  


class ChatResponse(BaseModel):
    response: str
    run_context: Optional[dict] = None  


async def get_run_context(run_id: str) -> dict | None:
    """Fetch healing run details from database for context."""
    try:
        supabase = get_supabase()
        result = supabase.table("healing_runs")\
            .select("*")\
            .eq("run_id", run_id)\
            .single()\
            .execute()
        
        if result.data and isinstance(result.data, dict):
            data = result.data
            return {
                "run_id": data.get("run_id"),
                "repo": data.get("repo_full_name"),
                "status": data.get("status"),
                "error_type": data.get("error_type"),
                "error_message": data.get("error_message"),
                "patient_zero": data.get("patient_zero"),
                "crash_site": data.get("crash_site"),
                "pr_url": data.get("pr_url"),
                "started_at": data.get("started_at"),
                "metadata": data.get("metadata", {}),
            }
        return None
    except Exception: 
        return None


async def get_run_events(run_id: str) -> list:
    """Fetch events from a healing run for detailed context."""
    try:
        supabase = get_supabase()
        result = supabase.table("healing_events")\
            .select("event_type, title, description, metadata")\
            .eq("run_id", run_id)\
            .order("created_at")\
            .execute()
        
        return result.data or []
    except Exception:  
        return []


@router.post("/", response_model=ChatResponse)
async def chat_with_talos(request: ChatRequest):
    """
    Chat with TALOS AI about healing runs and fixes.
    
    - Provide a message to ask questions
    - Optionally attach a run_id to discuss a specific fix
    - Conversation history is maintained for context
    """
    
    
    run_context = None
    context_block = ""
    
    if request.run_id:
        run_context = await get_run_context(request.run_id)
        events = await get_run_events(request.run_id)
        
        if run_context:
           
            meta = run_context.get('metadata') or {}
            
            context_block = f"""
═══════════════════════════════════════════════════════════════
ATTACHED HEALING RUN: {request.run_id}
═══════════════════════════════════════════════════════════════
Repository: {run_context.get('repo', 'Unknown')}
Status: {run_context.get('status', 'Unknown')}
Error Type: {run_context.get('error_type') or meta.get('error_type', 'Not classified')}
Error Message: {meta.get('error_message') or run_context.get('error_message', 'N/A')}
Patient Zero (Root Cause File): {run_context.get('patient_zero', 'Not identified')}
Crash Site: {meta.get('crash_site') or run_context.get('crash_site', 'Not identified')}
Project Type: {meta.get('project_type', 'Unknown')}
Test Command: {meta.get('test_command', 'Unknown')}
PR URL: {run_context.get('pr_url', 'No PR created')}
Started: {run_context.get('started_at', 'Unknown')}
Diagnosis: {meta.get('diagnosis', 'N/A')}
Modified Files: {meta.get('modified_files', [])}
Hot Files (Crash Sites): {meta.get('hot_files', [])}

═══════════════════════════════════════════════════════════════
ERROR LOG (what TALOS saw):
═══════════════════════════════════════════════════════════════
{meta.get('clean_error_log', 'Not available')[:2000]}

═══════════════════════════════════════════════════════════════
GIT DIFF (what changed):
═══════════════════════════════════════════════════════════════
{meta.get('diff_content', 'Not available')[:2000]}

═══════════════════════════════════════════════════════════════
GEMINI'S FIX PLAN:
═══════════════════════════════════════════════════════════════
{meta.get('fix_plan_summary', 'Not available')[:3000]}

═══════════════════════════════════════════════════════════════
HEALING TIMELINE (What TALOS did):
═══════════════════════════════════════════════════════════════
"""
            for event in events:
                context_block += f"• [{event.get('event_type', 'event')}] {event.get('title', '')}\n"
                if event.get('description'):
                    context_block += f"  {event.get('description')[:200]}...\n" if len(event.get('description', '')) > 200 else f"  {event.get('description')}\n"
            
            context_block += "═══════════════════════════════════════════════════════════════\n"
    
   
    system_prompt = f"""You are TALOS AI, an intelligent assistant that helps developers understand and learn from automated code fixes.

Your personality:
- Friendly and helpful, like a senior developer mentoring juniors
- Technical but accessible - explain complex concepts simply
- Proactive - suggest related improvements or learning opportunities
- Humble - acknowledge limitations and suggest when human review is needed
- Professional - avoid using emojis in responses

Your capabilities:
- Explain what went wrong in the code and why
- Break down the fix that was applied
- Teach debugging techniques and best practices
- Answer questions about error types, patterns, and prevention
- Discuss the healing process (cloning, analysis, fix, verification, PR)

{context_block if context_block else "No specific healing run is attached to this conversation. You can discuss TALOS in general or ask the user to attach a specific run."}

IMPORTANT RULES:
1. If asked about a specific fix but no run is attached, ask the user to attach one
2. Be concise but thorough - developers appreciate efficiency
3. Use code examples when helpful (use markdown code blocks)
4. If you don't know something, say so honestly
5. Always encourage the user to review fixes before merging
6. Do not use emojis in your responses - keep it professional

Respond in a conversational, helpful manner. You are TALOS, the autonomous healing agent."""

    
    conversation = []
    
    
    conversation.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=system_prompt)]
    ))
    conversation.append(types.Content(
        role="model", 
        parts=[types.Part.from_text(text="I understand. I'm TALOS AI, ready to help you understand code fixes and debugging. How can I assist you today?")]
    ))
    
   
    for msg in request.history[-10:]: 
        role = "user" if msg.role == "user" else "model"
        conversation.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg.content)]
        ))
    
    
    conversation.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=request.message)]
    ))

    try:
        
        current_key = key_rotator.get_current_key()
        client = genai.Client(api_key=current_key)
        
       
        import asyncio
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=MODEL_NAME,
                    contents=conversation,
                    config=types.GenerateContentConfig(
                        temperature=0.7,  
                        top_p=0.9,
                        max_output_tokens=1024,
                    )
                ),
                timeout=60.0  
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="The AI model took too long to respond. Please try again."
            )
        
        return ChatResponse(
            response=response.text,
            run_context=run_context
        )
        
    except Exception as e: 
        error_msg = str(e)
        
        
        if "429" in error_msg or "quota" in error_msg.lower():
            key_rotator.rotate()
            raise HTTPException(
                status_code=429, 
                detail="I'm a bit overwhelmed right now. Please try again in a moment!"
            ) from e
        
        raise HTTPException(
            status_code=500,
            detail="I encountered an error processing your message. Please try again."
        ) from e


@router.get("/health")
async def chat_health():
    """Check if chat service is available."""
    return {"status": "online", "model": MODEL_NAME}
