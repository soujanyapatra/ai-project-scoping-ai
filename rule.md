# Developer & Agent Rules: Scoping AI (FastAPI)

This guide documents the design standards and implementation rules for the `scoping-ai` FastAPI project.

---

## 1. Safe Template String Replacements
Never use Python's built-in `str.format()` on raw LLM prompt templates if those templates incorporate LLM outputs (such as complexity classification summaries or risk analysis tables) from prior steps.

* **Rule**: Always use manual `.replace("{placeholder}", value)` chains for substitution.

```python
# GOOD (Robust replacement)
prompt = prompt_template.replace("{classification}", step1_output)

# BAD (Will crash if step1_output contains "{")
prompt = prompt_template.format(classification=step1_output)
```

---

## 2. API Provider Abstraction
Maintain the dynamic LLM provider detection layer. All API calls must route through the `_stream_llm` coordinator to prevent codebase-wide refactoring when migrating between API providers (e.g., Anthropic, Gemini, OpenAI).

```python
def _detect_provider(self) -> str:
    # Identifies the LLM provider based on config model/base URI
    ...
```

* Add new provider endpoints by implementing localized private helpers (e.g. `_stream_anthropic`, `_stream_gemini`).
* Do not expose vendor-specific details inside the orchestrating `generate_scope` workflow.

---

## 3. SSE JSON Streaming Protocol
FastAPI handles Event-Source streams using the SSE format: `data: <json_string>\n\n`.
Ensure that:
* All step progress transitions are broadcasted with a structured type tag (e.g. `{"type": "step_start", "step": 1}`).
* Errors are caught globally in the stream generator and broadcasted as an error type chunk (e.g. `{"type": "error", "message": "..."}`) to prevent client connection hangs.
* Stream closures are flagged with a `{"type": "done"}` event.

---

## 4. Environment Configuration
* Keep environment variables generic. Do not prepend variables with `OPENAI_` or `GEMINI_` if they configure the primary engine. Use the `LLM_` prefix (`LLM_API_KEY`, `LLM_MODEL`, `LLM_API_BASE`).
* Load configuration variables via Pydantic `BaseSettings` (`app/core/config.py`) to guarantee strict typing and fallback defaults.
