import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.scope import ScopeRequest
from app.services.scope_service import ScopeService

router = APIRouter()
scope_service = ScopeService()

@router.post("/scope")
async def generate_scope(payload: ScopeRequest):
    async def event_generator():
        try:
            async for event in scope_service.generate_scope(payload):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")