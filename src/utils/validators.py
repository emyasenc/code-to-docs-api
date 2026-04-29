# src/utils/validators.py
"""
Input validation utilities for the Code-to-Docs API.
Ensures all user inputs are safe, properly formatted, and within limits.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


# GitHub URL patterns
GITHUB_URL_PATTERNS = [
    r'^https?://github\.com/[\w.-]+/[\w.-]+/?$',
    r'^https?://github\.com/[\w.-]+/[\w.-]+\.git/?$',
    r'^git@github\.com:[\w.-]+/[\w.-]+\.git$',
]

# Allowed frameworks (for future use)
ALLOWED_FRAMEWORKS = {
    'python', 'fastapi', 'django', 'flask',
    'javascript', 'react', 'nextjs', 'vue',
    'typescript', 'node', 'express',
    'go', 'rust', 'java', 'kotlin'
}


def validate_github_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a URL is a public GitHub repository.
    
    Args:
        url: GitHub repository URL
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "GitHub URL is required"
    
    url = url.strip()
    
    # Check against patterns
    for pattern in GITHUB_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return True, None
    
    return False, "Invalid GitHub URL. Must be a public GitHub repository (e.g., https://github.com/facebook/react)"


def sanitize_github_url(url: str) -> str:
    """
    Clean and normalize a GitHub URL.
    
    Args:
        url: Raw GitHub URL
    
    Returns:
        Normalized URL string
    """
    url = url.strip()
    
    # Remove trailing .git if present
    if url.endswith('.git'):
        url = url[:-4]
    
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    # Ensure https protocol (not git@)
    if url.startswith('git@github.com:'):
        # Convert git@github.com:user/repo -> https://github.com/user/repo
        path = url.replace('git@github.com:', '')
        url = f"https://github.com/{path}"
    
    if not url.startswith('http'):
        url = f"https://{url}"
    
    return url


def extract_repo_info(github_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract owner and repository name from GitHub URL.
    
    Args:
        github_url: Valid GitHub URL
    
    Returns:
        Tuple of (owner, repo_name) or (None, None) if invalid
    """
    is_valid, _ = validate_github_url(github_url)
    if not is_valid:
        return None, None
    
    sanitized = sanitize_github_url(github_url)
    parsed = urlparse(sanitized)
    path = parsed.path.strip('/')
    parts = path.split('/')
    
    if len(parts) >= 2:
        return parts[0], parts[1]
    
    return None, None


def validate_framework(framework: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a framework is supported.
    
    Args:
        framework: Framework name
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not framework:
        # Framework is optional, so empty is valid
        return True, None
    
    framework_lower = framework.lower()
    if framework_lower in ALLOWED_FRAMEWORKS:
        return True, None
    
    # Suggest close matches (bonus UX)
    close_matches = []
    for allowed in ALLOWED_FRAMEWORKS:
        if allowed.startswith(framework_lower) or framework_lower in allowed:
            close_matches.append(allowed)
    
    if close_matches:
        suggestion = f" Did you mean: {', '.join(close_matches[:3])}?"
    else:
        suggestion = ""
    
    return False, f"Unsupported framework '{framework}'.{suggestion}"


def validate_length(text: str, field_name: str, max_length: int = 10000) -> Tuple[bool, Optional[str]]:
    """
    Validate that a text field doesn't exceed maximum length.
    
    Args:
        text: The text to validate
        field_name: Name of the field (for error message)
        max_length: Maximum allowed length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return True, None
    
    if len(text) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"
    
    return True, None


def validate_code_input(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate code input (for future use).
    
    Args:
        code: Code snippet to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not code:
        return True, None
    
    # Check for suspicious patterns (basic injection protection)
    suspicious_patterns = [
        r'__import__\s*\(',
        r'exec\s*\(',
        r'eval\s*\(',
        r'os\.system\s*\(',
        r'subprocess\.',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False, "Code contains potentially unsafe patterns"
    
    return validate_length(code, "Code snippet", max_length=100000)


def validate_request_params(
    github_url: Optional[str] = None,
    code: Optional[str] = None,
    framework: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate all request parameters together.
    
    Args:
        github_url: GitHub repository URL
        code: Code snippet
        framework: Framework hint
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # At least one input must be provided
    if not github_url and not code:
        return False, "Either github_url or code must be provided"
    
    # Validate GitHub URL if provided
    if github_url:
        is_valid, error = validate_github_url(github_url)
        if not is_valid:
            return False, error
    
    # Validate framework if provided
    if framework:
        is_valid, error = validate_framework(framework)
        if not is_valid:
            return False, error
    
    # Validate code if provided
    if code:
        is_valid, error = validate_code_input(code)
        if not is_valid:
            return False, error
    
    return True, ""


def is_rate_limited(api_key: str, endpoint: str, request_count: int, limit: int = 10) -> bool:
    """
    Simple rate limiting check (in-memory).
    
    Args:
        api_key: User's API key
        endpoint: Endpoint being called
        request_count: Current request count in the window
        limit: Maximum allowed requests
    
    Returns:
        True if rate limited, False otherwise
    """
    return request_count >= limit