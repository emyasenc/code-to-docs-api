# src/services/github_service.py (FIXED VERSION)
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from git import Repo
import re
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    """Handle GitHub repository cloning and structure analysis"""
    
    def __init__(self, temp_dir: str = "/tmp/code-to-docs", github_token: Optional[str] = None):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.github_token = github_token
        
    async def clone_repo(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Clone a GitHub repository to a temporary directory."""
        try:
            # Parse GitHub URL to get repo name
            match = re.search(r"github\.com/([^/]+/[^/]+)/?", url)
            if not match:
                return None, "Invalid GitHub URL"
            
            repo_name = match.group(1).replace("/", "_")
            
            # Create unique temp directory
            clone_path = self.temp_dir / f"{repo_name}_{os.urandom(4).hex()}"
            
            # Clone with optional token for higher rate limits
            clone_url = url
            if self.github_token:
                clone_url = url.replace("https://", f"https://{self.github_token}@")
            
            logger.info(f"Cloning {url} to {clone_path}")
            Repo.clone_from(clone_url, clone_path, depth=1)
            
            return str(clone_path), None
            
        except Exception as e:
            logger.error(f"Failed to clone {url}: {e}")
            return None, f"Failed to clone repository: {str(e)}"
    
    async def get_repo_structure(self, repo_path: str) -> Dict:
        """Analyze repository structure"""
        structure = {
            "files": [],
            "directories": [],
            "languages": [],
            "main_files": []
        }
        
        main_patterns = ["main.py", "app.py", "server.py", "README.md"]
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git and __pycache__
            if ".git" in dirs:
                dirs.remove(".git")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            
            rel_path = Path(root).relative_to(repo_path)
            
            for file in files:
                file_path = Path(root) / file
                # FIX: Use Path(file_path) to get suffix properly
                ext = Path(file).suffix.lower()  # This was the bug!
                size = file_path.stat().st_size
                
                file_info = {
                    "path": str(rel_path / file) if rel_path != Path(".") else file,
                    "extension": ext,
                    "size": size,
                    "name": file
                }
                structure["files"].append(file_info)
                
                # Detect languages
                if ext == ".py":
                    if "python" not in structure["languages"]:
                        structure["languages"].append("python")
                elif ext in [".js"]:
                    if "javascript" not in structure["languages"]:
                        structure["languages"].append("javascript")
                elif ext in [".ts"]:
                    if "typescript" not in structure["languages"]:
                        structure["languages"].append("typescript")
                elif ext in [".md"]:
                    if "markdown" not in structure["languages"]:
                        structure["languages"].append("markdown")
                
                # Detect main files
                if file in main_patterns:
                    structure["main_files"].append(str(rel_path / file))
        
        return structure
    
    def cleanup(self, path: str):
        """Remove temporary directory"""
        if path and os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
                logger.info(f"Cleaned up {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")