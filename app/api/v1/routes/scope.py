import os
import json
import random
import asyncio
# Core FastAPI and routing dependencies
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.scope import ScopeRequest

router = APIRouter()

@router.post("/scope")
async def generate_scope(payload: ScopeRequest):
    async def event_generator():
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dump_path = os.path.abspath(os.path.join(current_dir, "../../../../dump_memory.json"))
            with open(dump_path, "r", encoding="utf-8") as f:
                templates = json.load(f)
            
            # Choose a random template
            template = random.choice(templates)
            
            # Formulate step contents based on payload
            project_type_label = payload.projectType.replace("_", " ").title()
            industry_label = payload.industry
            budget_label = f"${payload.budgetUsd:,.2f}" if payload.budgetUsd else "N/A"
            features_count = len(payload.features)
            
            step1_content = (
                f"Project Type: {project_type_label}\n"
                f"Industry: {industry_label}\n"
                f"Budget: {budget_label}\n\n"
                f"{template['classification']}"
            )
            
            step2_content = (
                f"Top risks for {project_type_label} in {industry_label} ({features_count} features listed):\n"
                f"{template['risks']}"
            )
            
            step3_content = (
                f"# Project Scope Document\n\n"
                f"## Profile\n"
                f"- **Type**: {project_type_label}\n"
                f"- **Industry**: {industry_label}\n"
                f"- **Platforms**: {', '.join(payload.platforms)}\n"
                f"- **Timeline**: {payload.timelineStart or 'N/A'} to {payload.timelineEnd or 'N/A'}\n\n"
                f"{template['document']}"
            )
            
            # Send step_start 1
            yield f"data: {json.dumps({'type': 'step_start', 'step': 1})}\n\n"
            await asyncio.sleep(0.5)
            
            # Send section 1
            yield f"data: {json.dumps({'type': 'section', 'step': 1, 'section': 'Complexity classification', 'content': step1_content})}\n\n"
            await asyncio.sleep(0.8)
            
            # Send step_start 2
            yield f"data: {json.dumps({'type': 'step_start', 'step': 2})}\n\n"
            await asyncio.sleep(0.5)
            
            # Send section 2
            yield f"data: {json.dumps({'type': 'section', 'step': 2, 'section': 'Feature risks', 'content': step2_content})}\n\n"
            await asyncio.sleep(0.8)
            
            # Send step_start 3
            yield f"data: {json.dumps({'type': 'step_start', 'step': 3})}\n\n"
            await asyncio.sleep(0.5)
            
            # Send section 3
            yield f"data: {json.dumps({'type': 'section', 'step': 3, 'section': 'Scope document', 'content': step3_content})}\n\n"
            await asyncio.sleep(0.8)
            
            # Send done
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")