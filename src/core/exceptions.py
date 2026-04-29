# src/core/exceptions.py
"""
Custom exceptions for the Code-to-Docs API.
"""

from fastapi import HTTPException, status

class CodeToDocsError(Exception):
    """Base exception for all API-specific errors."""
    pass

class GitHubCloneError(CodeToDocsError):
    """Raised when cloning a GitHub repository fails."""
    pass

class LLMServiceError(CodeToDocsError):
    """Raised when the LLM service (Groq, OpenAI) fails."""
    pass

class RateLimitExceeded(CodeToDocsError):
    """Raised when a user exceeds their rate limit."""
    pass

def raise_github_error(repo_url: str, detail: str) -> None:
    """Raise a formatted HTTPException for GitHub clone errors."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "GITHUB_CLONE_FAILED",
            "repo_url": repo_url,
            "message": detail,
            "suggestion": "Make sure the repository is public and the URL is correct."
        }
    )

def raise_llm_error(provider: str, detail: str) -> None:
    """Raise a formatted HTTPException for LLM service errors."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "LLM_SERVICE_UNAVAILABLE",
            "provider": provider,
            "message": detail,
            "suggestion": "Please try again later or check your API key."
        }
    )