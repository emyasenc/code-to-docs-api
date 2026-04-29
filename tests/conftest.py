# tests/conftest.py
"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_github_url():
    """Sample GitHub URL for testing"""
    return "https://github.com/octocat/Hello-World"


@pytest.fixture
def sample_code():
    """Sample code snippet for testing"""
    return """
def greet(name: str) -> str:
    \"\"\"Return a greeting message\"\"\"
    return f"Hello, {name}!"
"""