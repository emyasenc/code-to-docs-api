# src/api/v1/endpoints/generate.py
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
import logging
import traceback
import os

from src.models.schemas import GenerateRequest, GenerateResponse
from src.services.github_service import GitHubService
from src.services.code_parser import CodeParser
from src.utils.validators import (
    validate_request_params,
    sanitize_github_url,
    extract_repo_info
)
from src.services.cache_service import CacheService
from src.services.llm_service import LLMService
from src.config import get_settings
from src.api.dependencies import verify_api_key, get_user_identifier, rate_limit_dep
from src.core.exceptions import (
    GitHubCloneError,
    LLMServiceError,
    raise_github_error,
    raise_llm_error
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize cache service
cache_service = CacheService()


@router.post("/generate", response_model=GenerateResponse)
async def generate_docs(
    request: GenerateRequest,
    api_key: str = Depends(verify_api_key),
    user_id: str = Depends(get_user_identifier),
    _: str = Depends(rate_limit_dep)
):
    """Generate documentation using LLM"""
    
    # ============================================
    # STEP 1: Validate inputs
    # ============================================
    is_valid, error_msg = validate_request_params(
        github_url=str(request.github_url) if request.github_url else None,
        code=request.code,
        framework=request.framework
    )
    
    if not is_valid:
        logger.warning(f"Invalid request from {user_id}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # ============================================
    # STEP 2: Handle code input (if provided)
    # ============================================
    if request.code:
        return GenerateResponse(
            success=True,
            readme=f"# Documentation\n\n## Code Analysis\n\n```\n{request.code[:500]}\n```\n\nFull documentation generation for code snippets coming soon.",
            detected_framework=request.framework or "unknown",
            estimated_tokens=len(request.code) // 4,
            credits_used=1
        )
    
    # ============================================
    # STEP 3: Handle GitHub URL input
    # ============================================
    if not request.github_url:
        return GenerateResponse(
            success=True,
            readme="# README\n\nPlease provide a GitHub URL or code snippet.",
            detected_framework="unknown",
            estimated_tokens=0,
            credits_used=0
        )
    
    # Sanitize and normalize URL
    raw_url = str(request.github_url)
    sanitized_url = sanitize_github_url(raw_url)
    owner, repo_name = extract_repo_info(sanitized_url)
    
    logger.info(f"Processing request for repo: {owner}/{repo_name} (user: {user_id})")
    
    # ============================================
    # STEP 4: Check cache first
    # ============================================
    cached_result = cache_service.get(
        sanitized_url,
        request.include_readme,
        request.include_openapi,
        request.include_contributing,
        request.include_architecture
    )
    
    if cached_result:
        logger.info(f"Cache hit for {owner}/{repo_name}")
        return GenerateResponse(**cached_result)
    
    # ============================================
    # STEP 5: Initialize services
    # ============================================
    github_service = GitHubService(settings.TEMP_DIR, settings.GITHUB_TOKEN)
    code_parser = CodeParser()
    
    try:
        llm_service = LLMService()
    except Exception as e:
        logger.error(f"LLM Service init failed: {traceback.format_exc()}")
        raise_llm_error("Groq", str(e))
    
    repo_path = None
    
    try:
        # ============================================
        # STEP 6: Clone repository
        # ============================================
        repo_path, error = await github_service.clone_repo(sanitized_url)
        if error:
            raise_github_error(sanitized_url, error)
        
        # ============================================
        # STEP 7: Get repository structure and parse code
        # ============================================
        structure = await github_service.get_repo_structure(repo_path)
        
        # Parse code files
        file_contents = {}
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in code_parser.supported_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            rel_path = os.path.relpath(file_path, repo_path)
                            file_contents[rel_path] = f.read()
                    except:
                        pass
        
        # Extract summary with directory tree
        try:
            summary = code_parser.extract_summary(repo_path, file_contents)
            logger.info(f"Parsed {summary['total_files']} files, {summary['total_functions']} functions, {summary['total_classes']} classes")
        except Exception as e:
            logger.warning(f"Code parsing failed (non-fatal): {e}")
            summary = None
        
        # ============================================
        # STEP 8: Build enriched structure for LLM
        # ============================================
        enriched_structure = {
            "languages": structure.get('languages', []),
            "files": structure.get('files', []),
            "main_files": structure.get('main_files', []),
            "directory_tree": summary.get('directory_tree', 'No directory tree available') if summary else 'No directory tree available',
        }
        
        # ============================================
        # STEP 9: Generate README using LLM
        # ============================================
        try:
            readme_content = await llm_service.generate_readme(enriched_structure, repo_name)
        except Exception as e:
            raise_llm_error("Groq", str(e))
        
        # ============================================
        # STEP 10: Build response
        # ============================================
        response_data = {
            "success": True,
            "readme": readme_content,
            "openapi_spec": None,
            "contributing_guide": None,
            "architecture": None,
            "detected_framework": structure['languages'][0] if structure.get('languages') else "unknown",
            "estimated_tokens": len(readme_content) // 4,
            "credits_used": 1
        }
        
        # ============================================
        # STEP 11: Save to cache
        # ============================================
        cache_service.set(
            sanitized_url,
            response_data,
            request.include_readme,
            request.include_openapi,
            request.include_contributing,
            request.include_architecture
        )
        
        logger.info(f"Successfully generated documentation for {owner}/{repo_name}")
        
        return GenerateResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Generation failed for {owner}/{repo_name}: {error_detail}")
        raise HTTPException(status_code=500, detail=f"{str(e)} | Check logs for full traceback")
    
    finally:
        if repo_path:
            github_service.cleanup(repo_path)