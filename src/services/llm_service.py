# src/services/llm_service.py (FIXED)
import httpx
import logging
from typing import Optional
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMService:
    """Handles LLM API calls (Groq)"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"  # Updated model name
        self.base_url = "https://api.groq.com/openai/v1"
    
    async def generate_readme(self, repo_structure: dict, repo_name: str) -> str:
        """Generate a professional README using LLM"""
        
        if not self.api_key:
            return "⚠️ No Groq API key configured. Add GROQ_API_KEY to .env"
        
        # Build prompt with repo info
        files_list = ""
        for file in repo_structure.get('files', [])[:20]:
            files_list += f"- {file['path']}\n"
        
        prompt = f"""Generate a professional README.md for a GitHub repository called "{repo_name}".

Repository Info:
- Languages: {', '.join(repo_structure.get('languages', []))}
- Total Files: {len(repo_structure.get('files', []))}
- Main Files: {', '.join(repo_structure.get('main_files', []))}

Key Files:
{files_list}

Generate a complete README.md with:
1. Project Title (based on repo name)
2. Description of what this project does
3. Features
4. Tech Stack
5. Installation instructions
6. Usage examples
7. API endpoints (if applicable)

Make it professional and specific."""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are an expert technical writer. Generate clean, professional documentation."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = response.text
                    logger.error(f"Groq API error {response.status_code}: {error_text}")
                    return f"Error: API returned {response.status_code}. Check your API key and try again."
                    
            except Exception as e:
                logger.error(f"LLM error: {e}")
                return f"Error generating README: {str(e)}"