# src/services/code_parser.py
"""
Code parsing service for extracting meaningful information from source files.
Supports multiple languages and provides structured output for documentation.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CodeParser:
    """Parse source code files and extract structured information."""
    
    # Language-specific comment markers
    COMMENT_MARKERS = {
        '.py': '#',
        '.js': '//',
        '.ts': '//',
        '.jsx': '//',
        '.tsx': '//',
        '.go': '//',
        '.rs': '//',
        '.java': '//',
        '.c': '//',
        '.cpp': '//',
        '.h': '//',
        '.rb': '#',
        '.php': '//',
        '.sh': '#',
    }
    
    def __init__(self):
        self.supported_extensions = list(self.COMMENT_MARKERS.keys())
    
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a single file and extract structured information.
        
        Args:
            file_path: Path to the file (for extension detection)
            content: File content as string
        
        Returns:
            Dictionary with parsed information (functions, classes, imports, etc.)
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.py':
            return self._parse_python(content)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            return self._parse_javascript(content)
        else:
            return self._parse_generic(content, ext)
    
    def _parse_python(self, content: str) -> Dict[str, Any]:
        """Parse Python file using AST."""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
            "docstring": None,
            "complexity": "unknown"
        }
        
        # ========== FIX: Handle empty file ==========
        if not content or not content.strip():
            return result
        
        try:
            tree = ast.parse(content)
            
            # Extract docstring (only if tree.body has elements)
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
                result["docstring"] = tree.body[0].value.value
            
            for node in ast.walk(tree):
                # Functions
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node)
                    }
                    result["functions"].append(func_info)
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "lineno": node.lineno,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node)
                    }
                    result["classes"].append(class_info)
                
                # Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    result["imports"].append(f"{node.module}.{node.names[0].name}")
            
            # Rough complexity estimate based on function count
            if len(result["functions"]) > 10:
                result["complexity"] = "high"
            elif len(result["functions"]) > 5:
                result["complexity"] = "medium"
            else:
                result["complexity"] = "low"
                
        except SyntaxError as e:
            logger.warning(f"Python parsing failed: {e}")
            result["parse_error"] = str(e)
        
        return result
    
    def _parse_javascript(self, content: str) -> Dict[str, Any]:
        """Parse JavaScript/TypeScript file using regex patterns."""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "complexity": "unknown"
        }

        # Handle empty file
        if not content or not content.strip():
            return result

        # Function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\(?.*\)?\s*=>',
            r'async\s+function\s+(\w+)\s*\(',
        ]

        for pattern in func_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                result["functions"].append({"name": match, "lineno": 0})

        # Class patterns - more precise to avoid matching the word 'class' itself
        class_patterns = [
            r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{',
            r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s+extends\s+\w+\s*\{',
        ]

        class_names = set()
        for pattern in class_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                class_names.add(match)

        result["classes"] = list(class_names)

        # Import patterns
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"](.+)[\'"]',
            r'import\s+[\'"](.+)[\'"]',
            r'require\([\'"](.+)[\'"]\)',
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                result["imports"].append(match)

        # Export patterns
        export_patterns = [
            r'export\s+default\s+(\w+)',
            r'export\s+{\s*([^}]+)\s*}',
            r'export\s+(?:const|let|var|function|class)\s+(\w+)',
        ]

        for pattern in export_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                result["exports"].append(match if isinstance(match, str) else match[0])

        # Complexity estimate (MOVED OUTSIDE THE LOOP)
        total_items = len(result["functions"]) + len(result["classes"])
        if total_items > 15:
            result["complexity"] = "high"
        elif total_items > 8:
            result["complexity"] = "medium"
        else:
            result["complexity"] = "low"

        return result
    
    def _parse_generic(self, content: str, ext: str) -> Dict[str, Any]:
        """Generic parser for unsupported languages."""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
            "line_count": len(content.splitlines()),
            "complexity": "unknown"
        }
        
        # Handle empty file
        if not content or not content.strip():
            result["line_count"] = 0
            result["code_lines"] = 0
            return result
        
        # Count lines of code (excluding comments and blank lines)
        comment_marker = self.COMMENT_MARKERS.get(ext, '#')
        lines = content.splitlines()
        code_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(comment_marker):
                code_lines += 1
        
        result["code_lines"] = code_lines
        
        # Rough complexity based on line count
        if code_lines > 500:
            result["complexity"] = "very_high"
        elif code_lines > 200:
            result["complexity"] = "high"
        elif code_lines > 50:
            result["complexity"] = "medium"
        else:
            result["complexity"] = "low"
        
        return result
    
    def extract_summary(self, repo_path: str, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract a high-level summary of the entire repository.
        
        Args:
            repo_path: Path to the repository
            file_contents: Dictionary of {file_path: content}
        
        Returns:
            Summary dictionary with aggregated statistics
        """
        summary = {
            "total_files": len(file_contents),
            "total_code_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "languages": set(),
            "files_by_language": {},
            "complexity": "unknown",
            "directory_tree": ""
        }
        
        for file_path, content in file_contents.items():
            ext = Path(file_path).suffix.lower()
            if ext:
                summary["languages"].add(ext)
                summary["files_by_language"][ext] = summary["files_by_language"].get(ext, 0) + 1
            
            # Parse file to extract functions and classes
            parsed = self.parse_file(file_path, content)
            summary["total_functions"] += len(parsed.get("functions", []))
            summary["total_classes"] += len(parsed.get("classes", []))
            
            # Estimate code lines (simplified)
            summary["total_code_lines"] += len(content.splitlines())
        
        # Convert set to list for JSON serialization
        summary["languages"] = list(summary["languages"])
        
        # Overall complexity rating
        if summary["total_code_lines"] > 5000:
            summary["complexity"] = "very_high"
        elif summary["total_code_lines"] > 2000:
            summary["complexity"] = "high"
        elif summary["total_code_lines"] > 500:
            summary["complexity"] = "medium"
        else:
            summary["complexity"] = "low"
        
        # Add directory tree at the end
        try:
            summary["directory_tree"] = self.generate_directory_tree(repo_path)
        except Exception as e:
            logger.warning(f"Failed to generate directory tree: {e}")
            summary["directory_tree"] = "Could not generate directory tree"

        return summary
    
    def generate_directory_tree(self, repo_path: str, max_depth: int = 3, max_files: int = 50) -> str:
        """
        Generate a ASCII tree representation of the directory structure.
    
        Args:
            repo_path: Path to the repository root
            max_depth: Maximum directory depth to traverse
            max_files: Maximum number of files to include (prevents giant trees)
    
        Returns:
            ASCII tree string
        """
        import os
    
        def _generate_tree(path: str, prefix: str = "", depth: int = 0, file_count: int = 0) -> tuple[str, int]:
            if depth > max_depth or file_count > max_files:
                return "", file_count
        
            try:
                items = sorted(os.listdir(path))
            except PermissionError:
                return "", file_count
        
            # Separate directories and files
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item)) and not item.startswith('.')]
            files = [item for item in items if os.path.isfile(os.path.join(path, item)) and not item.startswith('.')]
        
            # Prioritize common root files (README, LICENSE, etc.)
            common_files = ['README.md', 'LICENSE', 'CONTRIBUTING.md', 'CHANGELOG.md']
            files.sort(key=lambda x: (0 if x in common_files else 1, x))
        
            result = ""
            all_items = dirs + files
        
            for i, item in enumerate(all_items):
                if file_count >= max_files:
                    break
            
                is_last = (i == len(all_items) - 1)
                current_prefix = "└── " if is_last else "├── "
                next_prefix = "    " if is_last else "│   "
            
                item_path = os.path.join(path, item)
                result += f"{prefix}{current_prefix}{item}\n"
                file_count += 1
            
                if os.path.isdir(item_path):
                    subtree, file_count = _generate_tree(item_path, prefix + next_prefix, depth + 1, file_count)
                    result += subtree
        
            return result, file_count
    
        # Start tree generation
        repo_name = os.path.basename(repo_path)
        tree, _ = _generate_tree(repo_path, "", 0, 0)
        return f"{repo_name}/\n{tree}"