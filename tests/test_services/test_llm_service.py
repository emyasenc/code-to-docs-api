"""
Tests for the LLM Service.
"""

import pytest
from unittest.mock import patch, MagicMock


# ========== Readme Generation Tests (Mocked) ==========

@pytest.mark.asyncio
async def test_generate_readme_success():
    """Test successful README generation."""
    with patch('src.services.llm_service.httpx.AsyncClient') as mock_client:
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "# Test Repository\n\nThis is a generated README."}}]
        }
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Create service with mock api_key
        from src.services.llm_service import LLMService
        service = LLMService()
        service.api_key = "fake_key"  # Bypass real config
        
        sample_structure = {"languages": ["python"], "files": [], "main_files": []}
        result = await service.generate_readme(sample_structure, "test-repo")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_readme_api_error():
    """Test that generate_readme handles API errors gracefully."""
    with patch('src.services.llm_service.httpx.AsyncClient') as mock_client:
        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        from src.services.llm_service import LLMService
        service = LLMService()
        service.api_key = "fake_key"
        
        sample_structure = {"languages": ["python"], "files": [], "main_files": []}
        result = await service.generate_readme(sample_structure, "test-repo")
        
        assert result is not None
        assert "Error: API returned 500" in result


@pytest.mark.asyncio
async def test_generate_readme_exception():
    """Test that generate_readme handles exceptions gracefully."""
    with patch('src.services.llm_service.httpx.AsyncClient') as mock_client:
        # Mock an exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Connection failed")
        
        from src.services.llm_service import LLMService
        service = LLMService()
        service.api_key = "fake_key"
        
        sample_structure = {"languages": ["python"], "files": [], "main_files": []}
        result = await service.generate_readme(sample_structure, "test-repo")
        
        assert result is not None
        assert "Error generating README" in result


@pytest.mark.asyncio
async def test_generate_readme_no_api_key():
    """Test README generation when API key is missing."""
    from src.services.llm_service import LLMService
    service = LLMService()
    service.api_key = None  # Simulate missing key
    
    sample_structure = {"languages": ["python"], "files": [], "main_files": []}
    result = await service.generate_readme(sample_structure, "test-repo")
    
    assert result is not None
    assert "No Groq API key configured" in result


@pytest.mark.asyncio
async def test_generate_readme_empty_structure():
    """Test README generation with empty structure."""
    with patch('src.services.llm_service.httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "# Empty Repo\n\nNo code found."}}]
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        from src.services.llm_service import LLMService
        service = LLMService()
        service.api_key = "fake_key"
        
        empty_structure = {"languages": [], "files": [], "main_files": []}
        result = await service.generate_readme(empty_structure, "empty-repo")
        
        assert result is not None
        assert isinstance(result, str)


@pytest.mark.asyncio
async def test_generate_readme_with_structure():
    """Test README generation with real structure data."""
    with patch('src.services.llm_service.httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "# Real Structure\n\nGenerated content."}}]
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        from src.services.llm_service import LLMService
        service = LLMService()
        service.api_key = "fake_key"
        
        sample_structure = {
            "languages": ["python", "javascript"],
            "files": [{"path": "main.py"}, {"path": "utils.js"}],
            "main_files": ["main.py"]
        }
        result = await service.generate_readme(sample_structure, "test-repo")
        
        assert result is not None
        assert isinstance(result, str)