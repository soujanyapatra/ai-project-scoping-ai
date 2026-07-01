import os
import json
import random
import asyncio
from typing import AsyncGenerator, Dict, Any
import httpx

from app.core.config import settings
from app.core.logger import logger
from app.schemas.scope import ScopeRequest

class ScopeService:
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.api_base = settings.llm_api_base

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _load_prompt(self, filename: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.abspath(os.path.join(current_dir, "../prompts", filename))
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        logger.warning(f"Prompt file not found at: {prompt_path}")
        return ""

    def _render_prompt(self, filename: str, context: dict) -> str:
        from jinja2 import Template
        template_content = self._load_prompt(filename)
        if not template_content:
            return ""
        template = Template(template_content)
        return template.render(**context)

    def _detect_provider(self) -> str:
        base_lower = self.api_base.lower()
        model_lower = self.model.lower()
        if "anthropic" in base_lower or "claude" in model_lower:
            return "anthropic"
        if "gemini" in base_lower or "google" in model_lower:
            return "gemini"
        return "openai"

    async def _stream_llm(self, messages: list) -> AsyncGenerator[str, None]:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            else:
                lc_messages.append(HumanMessage(content=msg["content"]))

        logger.info(f"Using LangChain ChatOpenAI stream with model {self.model} to {self.api_base}")
        
        async_client = httpx.AsyncClient(verify=settings.llm_verify_ssl)
        try:
            llm = ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.api_base,
                model_name=self.model,
                temperature=0.7,
                streaming=True,
                http_async_client=async_client
            )
            
            async for chunk in llm.astream(lc_messages):
                yield chunk.content
        finally:
            await async_client.aclose()

    async def generate_scope(self, payload: ScopeRequest) -> AsyncGenerator[Dict[str, Any], None]:
        # Formulate variables from payload
        project_type_label = payload.projectType.replace("_", " ").title()
        industry_label = payload.industry
        budget_label = f"${payload.budgetUsd:,.2f}" if payload.budgetUsd else "N/A"
        features_str = ", ".join(payload.features) if payload.features else "None"
        platforms_str = ", ".join(payload.platforms) if payload.platforms else "None"
        integrations_str = ", ".join(payload.integrations) if payload.integrations else "None"
        constraints_str = payload.constraints or "None"
        success_criteria_str = payload.successCriteria or "None"
        timeline_start = payload.timelineStart or "N/A"
        timeline_end = payload.timelineEnd or "N/A"

        if not self.is_configured():
            logger.warning("LLM API Key is not configured. Falling back to simulated streaming using template data.")
            async for event in self._generate_simulated_stream(payload):
                yield event
            return

        try:
            # ----------------------------------------------------
            # STEP 1: Complexity Classification
            # ----------------------------------------------------
            yield {"type": "step_start", "step": 1}
            await asyncio.sleep(0.01)

            classification_prompt = self._render_prompt(
                "classification.jinja",
                {
                    "project_type": project_type_label,
                    "industry": industry_label,
                    "budget": budget_label,
                    "platforms": platforms_str,
                    "timeline_start": str(timeline_start),
                    "timeline_end": str(timeline_end),
                    "features": features_str,
                    "integrations": integrations_str,
                    "constraints": constraints_str,
                    "success_criteria": success_criteria_str,
                }
            )

            messages = [
                {"role": "system", "content": "You are a professional project scoping assistant."},
                {"role": "user", "content": classification_prompt}
            ]

            step1_content = ""
            async for token in self._stream_llm(messages):
                step1_content += token
                yield {
                    "type": "section",
                    "step": 1,
                    "section": "Complexity classification",
                    "content": token
                }
            
            logger.info("Step 1 Classification completed.")
            await asyncio.sleep(0.01)

            # ----------------------------------------------------
            # STEP 2: Risks & Mitigations
            # ----------------------------------------------------
            yield {"type": "step_start", "step": 2}
            await asyncio.sleep(0.01)

            risks_prompt = self._render_prompt(
                "risks.jinja",
                {
                    "project_type": project_type_label,
                    "industry": industry_label,
                    "platforms": platforms_str,
                    "features": features_str,
                    "integrations": integrations_str,
                    "constraints": constraints_str,
                    "classification": step1_content,
                }
            )

            messages = [
                {"role": "system", "content": "You are a professional risk assessment assistant."},
                {"role": "user", "content": risks_prompt}
            ]

            step2_content = ""
            async for token in self._stream_llm(messages):
                step2_content += token
                yield {
                    "type": "section",
                    "step": 2,
                    "section": "Feature risks",
                    "content": token
                }

            logger.info("Step 2 Risks completed.")
            await asyncio.sleep(0.01)

            # ----------------------------------------------------
            # STEP 3: Scope Document
            # ----------------------------------------------------
            yield {"type": "step_start", "step": 3}
            await asyncio.sleep(0.01)

            scope_prompt = self._render_prompt(
                "project_scope.jinja",
                {
                    "project_type": project_type_label,
                    "industry": industry_label,
                    "platforms": platforms_str,
                    "timeline_start": str(timeline_start),
                    "timeline_end": str(timeline_end),
                    "features": features_str,
                    "integrations": integrations_str,
                    "constraints": constraints_str,
                    "classification": step1_content,
                    "risks": step2_content,
                }
            )

            messages = [
                {"role": "system", "content": "You are a professional technical architect and product owner."},
                {"role": "user", "content": scope_prompt}
            ]

            step3_content = ""
            async for token in self._stream_llm(messages):
                step3_content += token
                yield {
                    "type": "section",
                    "step": 3,
                    "section": "Scope document",
                    "content": token
                }

            logger.info("Step 3 Scope Document completed.")
            await asyncio.sleep(0.01)

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Error in LLM streaming: {e}", exc_info=True)
            err_str = str(e)
            if "rate_limit" in err_str or "429" in err_str:
                user_msg = "Rate limit exceeded. Please wait a few seconds before trying again."
            elif "CERTIFICATE_VERIFY_FAILED" in err_str:
                user_msg = "SSL Certificate verification failed. Please try again."
            else:
                user_msg = "Generation failed. Please check your credentials and try again."
            yield {"type": "error", "message": user_msg}

    async def _generate_simulated_stream(self, payload: ScopeRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Graceful simulated streaming fallback if no API key is set.
        Generates realistic typing effects using local template.
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dump_path = os.path.abspath(os.path.join(current_dir, "../../dump_memory.json"))
            
            with open(dump_path, "r", encoding="utf-8") as f:
                templates = json.load(f)
            
            template = random.choice(templates)
            
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

            # --- Stream Step 1 ---
            yield {"type": "step_start", "step": 1}
            await asyncio.sleep(0.5)
            yield {
                "type": "section",
                "step": 1,
                "section": "Complexity classification",
                "content": step1_content
            }
            await asyncio.sleep(0.5)

            # --- Stream Step 2 ---
            yield {"type": "step_start", "step": 2}
            await asyncio.sleep(0.5)
            yield {
                "type": "section",
                "step": 2,
                "section": "Feature risks",
                "content": step2_content
            }
            await asyncio.sleep(0.5)

            # --- Stream Step 3 ---
            yield {"type": "step_start", "step": 3}
            await asyncio.sleep(0.5)
            yield {
                "type": "section",
                "step": 3,
                "section": "Scope document",
                "content": step3_content
            }
            await asyncio.sleep(0.5)

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Error in simulated stream: {e}", exc_info=True)
            yield {"type": "error", "message": f"Simulated Scoping Failed: {str(e)}"}

    async def _simulate_typing(self, text: str, step: int, section: str) -> AsyncGenerator[Dict[str, Any], None]:
        accumulated = ""
        chunk_size = 12
        for i in range(0, len(text), chunk_size):
            accumulated += text[i:i+chunk_size]
            yield {
                "type": "section",
                "step": step,
                "section": section,
                "content": accumulated
            }
            await asyncio.sleep(0.015)
