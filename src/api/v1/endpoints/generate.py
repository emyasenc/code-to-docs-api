# src/api/v1/endpoints/generate.py (updated with LLM)
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging

from src.models.schemas import GenerateRequest, GenerateResponse
from src.services.github_service import GitHubService
from src.services.llm_service import LLMService
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

@router.post("/generate", response_model=GenerateResponse)
async def generate_docs(
    request: GenerateRequest,
    api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Generate documentation using LLM"""
    
    if not request.github_url:
        return GenerateResponse(
            success=True,
            readme="# README\n\nPlease provide a GitHub URL.",
            detected_framework="unknown",
            estimated_tokens=0,
            credits_used=0
        )
    
    github_service = GitHubService(settings.TEMP_DIR, settings.GITHUB_TOKEN)
    llm_service = LLMService()
    repo_path = None
    
    try:
        # Clone the repository
        repo_path, error = await github_service.clone_repo(str(request.github_url))
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        # Get repository structure
        structure = await github_service.get_repo_structure(repo_path)
        
        # Extract repo name from URL
        repo_name = str(request.github_url).split("/")[-1].replace(".git", "")
        
        # Generate README using LLM
        readme_content = await llm_service.generate_readme(structure, repo_name)
        
        return GenerateResponse(
            success=True,
            readme=readme_content,
            detected_framework=structure['languages'][0] if structure['languages'] else "unknown",
            estimated_tokens=len(readme_content) // 4,
            credits_used=1
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if repo_path:
            github_service.cleanup(repo_path)