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

    def _detect_provider(self) -> str:
        base_lower = self.api_base.lower()
        model_lower = self.model.lower()
        if "anthropic" in base_lower or "claude" in model_lower:
            return "anthropic"
        if "gemini" in base_lower or "google" in model_lower:
            return "gemini"
        return "openai"

    async def _stream_llm(self, messages: list) -> AsyncGenerator[str, None]:
        provider = self._detect_provider()
        logger.info(f"Detected LLM provider: {provider} (model: {self.model})")
        if provider == "anthropic":
            async for token in self._stream_anthropic(messages):
                yield token
        elif provider == "gemini":
            async for token in self._stream_gemini(messages):
                yield token
        else:
            async for token in self._stream_openai(messages):
                yield token

    async def _stream_openai(self, messages: list) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:9000",
            "X-Title": "Project Scoping Tool",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
        }

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        logger.info(f"Initiating OpenAI/OpenRouter stream with model {self.model} to {url}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    err_msg = error_text.decode("utf-8", errors="ignore")
                    logger.error(f"OpenAI/OpenRouter error status {response.status_code}: {err_msg}")
                    raise Exception(f"OpenAI/OpenRouter API returned status {response.status_code}: {err_msg}")

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data_content = line[5:].strip()
                            if data_content == "[DONE]":
                                break
                            try:
                                data_json = json.loads(data_content)
                                if "choices" in data_json and len(data_json["choices"]) > 0:
                                    delta = data_json["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except Exception as e:
                                continue

    async def _stream_anthropic(self, messages: list) -> AsyncGenerator[str, None]:
        # Placeholder for future Claude integration
        if False:
            yield ""

    async def _stream_gemini(self, messages: list) -> AsyncGenerator[str, None]:
        # Placeholder for future Gemini integration
        if False:
            yield ""

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
            await asyncio.sleep(0.1)

            classification_prompt_tmpl = self._load_prompt("classification.txt")
            classification_prompt = (
                classification_prompt_tmpl
                .replace("{project_type}", project_type_label)
                .replace("{industry}", industry_label)
                .replace("{budget}", budget_label)
                .replace("{platforms}", platforms_str)
                .replace("{timeline_start}", str(timeline_start))
                .replace("{timeline_end}", str(timeline_end))
                .replace("{features}", features_str)
                .replace("{integrations}", integrations_str)
                .replace("{constraints}", constraints_str)
                .replace("{success_criteria}", success_criteria_str)
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
                    "content": step1_content
                }
            
            logger.info("Step 1 Classification completed.")
            await asyncio.sleep(0.5)

            # ----------------------------------------------------
            # STEP 2: Risks & Mitigations
            # ----------------------------------------------------
            yield {"type": "step_start", "step": 2}
            await asyncio.sleep(0.1)

            risks_prompt_tmpl = self._load_prompt("risks.txt")
            risks_prompt = (
                risks_prompt_tmpl
                .replace("{project_type}", project_type_label)
                .replace("{industry}", industry_label)
                .replace("{platforms}", platforms_str)
                .replace("{features}", features_str)
                .replace("{integrations}", integrations_str)
                .replace("{constraints}", constraints_str)
                .replace("{classification}", step1_content)
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
                    "content": step2_content
                }

            logger.info("Step 2 Risks completed.")
            await asyncio.sleep(0.5)

            # ----------------------------------------------------
            # STEP 3: Scope Document
            # ----------------------------------------------------
            yield {"type": "step_start", "step": 3}
            await asyncio.sleep(0.1)

            scope_prompt_tmpl = self._load_prompt("project_scope.txt")
            scope_prompt = (
                scope_prompt_tmpl
                .replace("{project_type}", project_type_label)
                .replace("{industry}", industry_label)
                .replace("{platforms}", platforms_str)
                .replace("{timeline_start}", str(timeline_start))
                .replace("{timeline_end}", str(timeline_end))
                .replace("{features}", features_str)
                .replace("{integrations}", integrations_str)
                .replace("{constraints}", constraints_str)
                .replace("{classification}", step1_content)
                .replace("{risks}", step2_content)
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
                    "content": step3_content
                }

            logger.info("Step 3 Scope Document completed.")
            await asyncio.sleep(0.5)

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Error in LLM streaming: {e}", exc_info=True)
            yield {"type": "error", "message": f"LLM Scoping Failed: {str(e)}"}

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
            await asyncio.sleep(0.2)
            async for event in self._simulate_typing(step1_content, 1, "Complexity classification"):
                yield event
            await asyncio.sleep(0.5)

            # --- Stream Step 2 ---
            yield {"type": "step_start", "step": 2}
            await asyncio.sleep(0.2)
            async for event in self._simulate_typing(step2_content, 2, "Feature risks"):
                yield event
            await asyncio.sleep(0.5)

            # --- Stream Step 3 ---
            yield {"type": "step_start", "step": 3}
            await asyncio.sleep(0.2)
            async for event in self._simulate_typing(step3_content, 3, "Scope document"):
                yield event
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
