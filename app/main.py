from fastapi import FastAPI
from app.api.v1.routes.scope import router as scope_router

app = FastAPI(
    title="AI Voice Agent",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": "Project Scoping AI API is running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}


# Register all api routes
app.include_router(
    scope_router, prefix="/api/v1"
)