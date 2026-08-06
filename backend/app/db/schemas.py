"""
Pydantic Schemas for Complaint Copilot AI
Request & Response models for API routes.
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
