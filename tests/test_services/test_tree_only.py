#!/usr/bin/env python3
"""
Test script to verify directory tree generation without LLM.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the project root to PYTHONPATH in case
os.chdir(project_root)

from src.services.code_parser import CodeParser
from src.services.github_service import GitHubService
from src.config import get_settings

settings = get_settings()


async def test_tree():
    """Clone a repo and print its directory tree."""
    
    github_service = GitHubService(settings.TEMP_DIR, settings.GITHUB_TOKEN)
    code_parser = CodeParser()
    
    # Test with your own API repo (has good structure)
    repo_url = "https://github.com/emyasenc/phone-validation-api"
    
    print(f"\n📦 Cloning {repo_url} ...")
    repo_path, error = await github_service.clone_repo(repo_url)
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Cloned to: {repo_path}")
    
    # Collect file contents
    file_contents = {}
    print("📁 Reading files...")
    
    for root, dirs, files in os.walk(repo_path):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            # Only parse code files
            if any(file.endswith(ext) for ext in code_parser.supported_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rel_path = os.path.relpath(file_path, repo_path)
                        file_contents[rel_path] = f.read()
                except Exception as e:
                    print(f"  ⚠️ Could not read {file}: {e}")
    
    print(f"📄 Found {len(file_contents)} files")
    
    # Extract summary with directory tree
    summary = code_parser.extract_summary(repo_path, file_contents)
    
    print("\n" + "=" * 60)
    print("🌲 DIRECTORY TREE")
    print("=" * 60)
    print(summary.get('directory_tree', 'No tree generated'))
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {summary['total_files']}")
    print(f"   Languages: {summary['languages']}")
    print(f"   Complexity: {summary['complexity']}")
    
    # Cleanup
    github_service.cleanup(repo_path)
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(test_tree())