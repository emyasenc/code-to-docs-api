# src/services/llm_service.py
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
        self.model = "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1"
    
    async def generate_readme(self, repo_structure: dict, repo_name: str) -> str:
        """Generate a professional README using LLM"""
        
        if not self.api_key:
            return "⚠️ No Groq API key configured. Add GROQ_API_KEY to .env"
        
        # Get directory tree from the structure
        directory_tree = repo_structure.get('directory_tree', 'No directory structure available')
        
        # Limit tree size (first 2000 chars to avoid huge prompts)
        if len(directory_tree) > 2000:
            directory_tree = directory_tree[:2000] + "\n... (truncated)"
        
        # Build files list
        files_list = ""
        for file in repo_structure.get('files', [])[:20]:
            files_list += f"- {file['path']}\n"
        
        prompt = f"""Generate a professional README.md for a GitHub repository called "{repo_name}".

Repository Structure (directory tree):

{directory_tree}


Repository Info:
- Languages: {', '.join(repo_structure.get('languages', []))}
- Total Files: {len(repo_structure.get('files', []))}
- Main Files: {', '.join(repo_structure.get('main_files', []))}

Key Files:
{files_list}
Generate a complete README.md with the following sections:
1. Project Title (based on repo name)
2. Description
3. Features
4. Tech Stack
5. **Project Structure** (use the directory tree above, format it as a code block)
6. Installation instructions
7. Usage examples
8. Contributing
9. License

IMPORTANT: Include the actual directory tree in the "Project Structure" section. Make it professional and specific to this repository."""
        
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
                            {"role": "system", "content": "You are an expert technical writer. Generate clean, professional documentation. ALWAYS include the provided directory tree in a 'Project Structure' section as a code block."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
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