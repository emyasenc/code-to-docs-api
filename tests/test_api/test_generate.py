"""
Tests for the documentation generation endpoint using requests.
"""

import pytest
import requests
import time
import threading
import uvicorn
from src.main import app

TEST_PORT = 8001
BASE_URL = f"http://localhost:{TEST_PORT}"


def run_server():
    """Run the FastAPI server in a background thread."""
    uvicorn.run(app, host="127.0.0.1", port=TEST_PORT, log_level="error")


@pytest.fixture(scope="module")
def live_server():
    """Start a live test server once before all tests."""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    # Wait for server to be ready
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=1)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    yield
    # thread is daemon, will exit automatically


class TestGenerateEndpoint:
    """Test suite for POST /api/v1/generate"""

    def test_generate_with_code_only(self, live_server):
        """Test response when only code is provided (should work)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "code": "def hello():\n    return 'world'",
                "framework": "python"
            }
        )
    
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Documentation" in data["readme"]
    
    def test_generate_with_valid_github_url(self, live_server):
        """Test successful generation with a valid GitHub URL"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "github_url": "https://github.com/facebook/react",
                "include_readme": True,
                "include_openapi": False,
                "include_contributing": False,
                "include_architecture": False
            },
            timeout=60
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "readme" in data
        assert data["detected_framework"] is not None

    def test_generate_with_invalid_github_url(self, live_server):
        """Test error handling for invalid GitHub URL"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "github_url": "https://github.com/not-a-valid-repo-12345",
                "include_readme": True
            }
        )

        assert response.status_code == 400
        data = response.json()
        # Different possible error formats
        assert "error" in str(data) or "Invalid" in str(data)

    def test_generate_without_github_url(self, live_server):
        """Test response when no GitHub URL or code is provided"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "include_readme": True
            }
        )
    
        # API correctly returns 400 when both github_url and code are missing
        assert response.status_code == 400
        data = response.json()
        assert "Either github_url or code must be provided" in str(data)

    def test_generate_with_code_snippet(self, live_server):
        """Test response when code snippet is provided"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "code": "def hello():\n    return 'world'",
                "framework": "python"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Documentation" in data["readme"]

    def test_generate_with_malformed_url(self, live_server):
        """Test error handling for malformed URL"""
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "github_url": "not a url",
                "include_readme": True
            }
        )

        # Should be 400 or 422 depending on validation
        assert response.status_code in [400, 422]

    def test_generate_health_check(self, live_server):
        """Test health check endpoint works"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_generate_root_endpoint(self, live_server):
        """Test root endpoint returns API info"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestGenerateIntegration:
    """Integration tests that require real external services"""

    @pytest.mark.slow
    def test_small_repo_performance(self, live_server):
        """Test performance on a small repository"""
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v1/generate",
            json={
                "github_url": "https://github.com/octocat/Hello-World",
                "include_readme": True
            },
            timeout=60
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should complete within 45 seconds (generous for LLM call)
        assert elapsed < 45, f"Request took {elapsed:.2f} seconds"