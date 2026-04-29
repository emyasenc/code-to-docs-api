# src/models/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List

class GenerateRequest(BaseModel):
    """Request to generate documentation"""
    
    github_url: Optional[HttpUrl] = None
    code: Optional[str] = None
    
    include_readme: bool = True
    include_openapi: bool = True
    include_contributing: bool = True
    include_architecture: bool = True
    
    framework: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/emyasenc/job-scam-detector",
                "include_readme": True,
                "include_openapi": True
            }
        }

class GenerateResponse(BaseModel):
    """Response with generated documentation"""
    
    success: bool
    readme: Optional[str] = None
    openapi_spec: Optional[Dict[str, Any]] = None
    contributing_guide: Optional[str] = None
    architecture: Optional[str] = None
    detected_framework: Optional[str] = None
    estimated_tokens: int
    credits_used: int