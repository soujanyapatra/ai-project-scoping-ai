from pydantic import BaseModel
from typing import List, Optional

class ScopeRequest(BaseModel):
    projectType: str
    industry: str
    budgetUsd: Optional[float] = None
    timelineStart: Optional[str] = None
    timelineEnd: Optional[str] = None
    features: List[str]
    platforms: List[str]
    integrations: Optional[List[str]] = None
    constraints: Optional[str] = None
    successCriteria: Optional[str] = None
