# AI Project Scoping - FastAPI Backend Engine

This repository contains the FastAPI-based backend engine for the **AI Project Scoping Tool**. It processes detailed discovery payloads and yields structured scoping results (classification, risk analysis, stack choices, timelines) as an event stream.

---

## 🚀 Overview

The FastAPI engine is designed to act as the reasoning and processing layer.
- **Current Mode**: For testing and early integration, it reads structured mockup scopes from `dump_memory.json`, dynamically populates them with the user's project parameters (type, industry, budget, timeline, and features count), and streams them step-by-step using **Server-Sent Events (SSE)**.
- **Future Mode**: Connects to LLM chain APIs (e.g. LangChain / OpenAI / Gemini) to dynamically draft the scope documents.

---

## 📂 Project Structure

```
ai-project-scoping-ai/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routes/
│   │       │   ├── estimate.py
│   │       │   ├── health.py
│   │       │   ├── requirements.py
│   │       │   └── scope.py       # Main scoping streaming logic
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── schemas/
│   │   └── scope.py               # Pydantic request models
│   └── main.py                    # App entry point
├── dump_memory.json               # Rich mock scoping templates database
├── requirements.txt               # Dependencies
└── README.md
```

---

## 🛠️ Getting Started

### 1. Prerequisite Packages
Ensure you have Python 3.8+ installed on your system.

### 2. Setup the Virtual Environment
Recreate the virtual environment and install the required modules:
```bash
# Re-create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Development Server
Launch the FastAPI application on port `9000` (the default port configured in the Laravel frontend):
```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

---

## 🔌 API Documentation

### 1. Health Status
Check if the service is running correctly.

* **Endpoint**: `GET /health`
* **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### 2. Scoping Stream
Initiates the scoping analysis. Returns a streaming `text/event-stream` response.

* **Endpoint**: `POST /api/v1/scope`
* **Content-Type**: `application/json`
* **Request Payload**:
  ```json
  {
    "projectType": "web_app",
    "industry": "healthcare",
    "budgetUsd": 50000.0,
    "timelineStart": "2026-06-16",
    "timelineEnd": "2026-07-16",
    "features": ["auth", "dashboard"],
    "platforms": ["web"],
    "integrations": ["stripe"],
    "constraints": "Strict budget",
    "successCriteria": "Converts users"
  }
  ```

* **Server-Sent Events (SSE) Flow**:
  1. `data: {"type": "step_start", "step": 1}` — Indicates step 1 is beginning.
  2. `data: {"type": "section", "step": 1, "section": "Complexity classification", "content": "..."}` — Sends Step 1 results.
  3. `data: {"type": "step_start", "step": 2}` — Indicates step 2 is beginning.
  4. `data: {"type": "section", "step": 2, "section": "Feature risks", "content": "..."}` — Sends Step 2 results.
  5. `data: {"type": "step_start", "step": 3}` — Indicates step 3 is beginning.
  6. `data: {"type": "section", "step": 3, "section": "Scope document", "content": "..."}` — Sends the final markdown document.
  7. `data: {"type": "done"}` — Stream completed.
