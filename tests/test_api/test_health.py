"""
Tests for the health check and root endpoints.
"""

import pytest
import requests
import time
import threading
import uvicorn
from src.main import app

TEST_PORT = 8002  # Different port to avoid conflicts with other test files
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


class TestHealthEndpoint:
    """Test suite for health check endpoints."""

    def test_health_endpoint_returns_200(self, live_server):
        """Test that /health returns 200 OK"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_correct_json(self, live_server):
        """Test that /health returns the expected JSON structure"""
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_endpoint_content_type(self, live_server):
        """Test that /health returns application/json"""
        response = requests.get(f"{BASE_URL}/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_root_endpoint_returns_200(self, live_server):
        """Test that / returns 200 OK"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200

    def test_root_endpoint_returns_api_info(self, live_server):
        """Test that / returns the expected API information"""
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_endpoint_content_type(self, live_server):
        """Test that / returns application/json"""
        response = requests.get(f"{BASE_URL}/")
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_endpoint_response_time(self, live_server):
        """Test that health check responds quickly"""
        import time
        start = time.time()
        response = requests.get(f"{BASE_URL}/health")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 0.5, f"Health check took {elapsed:.2f}s (should be <0.5s)"

    def test_root_endpoint_response_time(self, live_server):
        """Test that root endpoint responds quickly"""
        import time
        start = time.time()
        response = requests.get(f"{BASE_URL}/")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 0.1, f"Root endpoint took {elapsed:.2f}s (should be <0.1s)"


class TestHealthEndpointIntegration:
    """Integration tests that verify the API is operational."""

    def test_server_is_operational(self, live_server):
        """Test that both health and root endpoints work together"""
        health_response = requests.get(f"{BASE_URL}/health")
        root_response = requests.get(f"{BASE_URL}/")
        assert health_response.status_code == 200
        assert root_response.status_code == 200
        assert health_response.json().get("status") == "healthy"
        assert root_response.json().get("name") is not None

    @pytest.mark.parametrize("endpoint", ["/health", "/"])
    def test_all_health_endpoints_are_accessible(self, live_server, endpoint):
        """Test that all health-related endpoints are accessible"""
        response = requests.get(f"{BASE_URL}{endpoint}")
        assert response.status_code == 200