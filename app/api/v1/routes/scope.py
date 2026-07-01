import json
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.schemas.scope import ScopeRequest
from app.services.scope_service import ScopeService

router = APIRouter()
scope_service = ScopeService()

# Simple in-memory session cache with TTL (1 hour)
class SessionCache:
    def __init__(self):
        self._cache = {}

    def set(self, session_id: str, data: ScopeRequest, ttl: int = 3600):
        self._cache[session_id] = {
            "data": data,
            "expires_at": time.time() + ttl
        }

    def get(self, session_id: str) -> ScopeRequest:
        self.cleanup()
        item = self._cache.get(session_id)
        if item and item["expires_at"] > time.time():
            return item["data"]
        return None

    def cleanup(self):
        now = time.time()
        expired = [k for k, v in self._cache.items() if v["expires_at"] < now]
        for k in expired:
            del self._cache[k]

session_cache = SessionCache()

class InitiateRequest(BaseModel):
    session_id: str
    payload: ScopeRequest

@router.post("/scope/initiate")
async def initiate_scope(data: InitiateRequest):
    session_cache.set(data.session_id, data.payload)
    return {"status": "success", "session_id": data.session_id}

@router.get("/scope/stream/{session_id}")
async def stream_scope(session_id: str):
    payload = session_cache.get(session_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    async def event_generator():
        try:
            async for event in scope_service.generate_scope(payload):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/scope")
async def generate_scope(payload: ScopeRequest):
    async def event_generator():
        try:
            async for event in scope_service.generate_scope(payload):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")