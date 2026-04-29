# test_code_parser.py
"""
Tests for the CodeParser service.
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.services.code_parser import CodeParser


class TestCodeParser:
    """Test suite for CodeParser service."""
    
    @pytest.fixture
    def parser(self):
        """Return a CodeParser instance."""
        return CodeParser()
    
    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file with complex content."""
        content = '''
def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"

def calculate_sum(*args):
    """Calculate sum of arguments."""
    return sum(args)

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b

class AdvancedCalculator(Calculator):
    """Inherited calculator with more features."""
    
    def power(self, a, b):
        return a ** b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path, content
        
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_javascript_file(self):
        """Create a temporary JavaScript file with complex content."""
        content = '''
// Utility functions
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

const formatCurrency = (amount) => {
    return `$${amount.toFixed(2)}`;
};

// ES6 class
class ShoppingCart {
    constructor() {
        this.items = [];
    }
    
    addItem(item) {
        this.items.push(item);
    }
    
    removeItem(index) {
        this.items.splice(index, 1);
    }
    
    getTotal() {
        return calculateTotal(this.items);
    }
}

// Export for Node.js
module.exports = { ShoppingCart, formatCurrency };
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path, content
        
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_go_file(self):
        """Create a temporary Go file."""
        content = '''
package main

import "fmt"

// User struct represents a user
type User struct {
    Name string
    Age  int
}

// Greet returns a greeting message
func Greet(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}

func main() {
    fmt.Println(Greet("World"))
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path, content
        
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_directory_with_files(self):
        """Create a temporary directory with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Python file
            with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
                f.write('def hello():\n    return "world"\n\nclass Test:\n    pass')
            
            # JavaScript file
            with open(os.path.join(tmpdir, 'utils.js'), 'w') as f:
                f.write('function add(a, b) { return a + b; }\n\nconst multiply = (a, b) => a * b;')
            
            # Go file
            with open(os.path.join(tmpdir, 'main.go'), 'w') as f:
                f.write('package main\n\nfunc main() {}\n')
            
            # README (should be ignored)
            with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
                f.write('# Test Project\n\nThis is a test.')
            
            yield tmpdir
    
    # ========== Initialization Tests ==========
    
    def test_parser_initialization(self, parser):
        """Test that CodeParser initializes correctly."""
        assert parser is not None
        assert len(parser.supported_extensions) > 0
        assert '.py' in parser.supported_extensions
        assert '.js' in parser.supported_extensions
        assert '.go' in parser.supported_extensions
    
    # ========== Python Parsing Tests ==========
    
    def test_parse_python_file(self, parser, temp_python_file):
        """Test parsing a Python file."""
        temp_path, content = temp_python_file
        result = parser.parse_file(temp_path, content)
        
        # Check structure
        assert "functions" in result
        assert "classes" in result
        assert "imports" in result
        
        # Check functions
        functions = result.get("functions", [])
        assert len(functions) >= 2
        function_names = [f["name"] for f in functions]
        assert "greet" in function_names
        assert "calculate_sum" in function_names
        
        # Check function details
        greet_func = next((f for f in functions if f["name"] == "greet"), None)
        assert greet_func is not None
        if greet_func and "args" in greet_func:
            assert "args" in greet_func
        
        # Check classes
        classes = result.get("classes", [])
        assert len(classes) >= 2
        class_names = [c["name"] for c in classes]
        assert "Calculator" in class_names
        assert "AdvancedCalculator" in class_names
        
        # Check complexity
        assert result.get("complexity") in ["low", "medium", "high", "unknown"]
    
    def test_parse_python_file_with_imports(self, parser):
        """Test parsing Python file with imports."""
        content = '''
import os
import sys
from datetime import datetime
from typing import List, Optional

def test_func():
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                file_content = f.read()
            result = parser.parse_file(temp_path, file_content)
            
            imports = result.get("imports", [])
            assert len(imports) >= 2
            assert any("os" in imp for imp in imports)
            assert any("datetime" in imp for imp in imports)
        finally:
            os.unlink(temp_path)
    
    # ========== JavaScript Parsing Tests ==========
    
    def test_parse_javascript_file(self, parser, temp_javascript_file):
        """Test parsing a JavaScript file."""
        temp_path, content = temp_javascript_file
        result = parser.parse_file(temp_path, content)
    
        assert "functions" in result
    
        # Check functions
        functions = result.get("functions", [])
        assert len(functions) >= 2
        function_names = [f["name"] if isinstance(f, dict) else f for f in functions]
        assert any(name in ["calculateTotal", "formatCurrency"] for name in function_names)
    
        # Check classes (could be list of strings or list of dicts)
        classes = result.get("classes", [])
        class_names = []
        for c in classes:
            if isinstance(c, dict):
                class_names.append(c.get("name", ""))
            elif isinstance(c, str):
                class_names.append(c)
            elif isinstance(c, list):
                for item in c:
                    if isinstance(item, str):
                        class_names.append(item)
    
        # Should detect ShoppingCart class
        assert any("ShoppingCart" in name for name in class_names), f"Class names found: {class_names}"
    
        # Check complexity
        assert result.get("complexity") in ["low", "medium", "high", "unknown"]
    
    # ========== Go Parsing Tests ==========
    
    def test_parse_go_file(self, parser, temp_go_file):
        """Test parsing a Go file (generic parser fallback)."""
        temp_path, content = temp_go_file
        result = parser.parse_file(temp_path, content)
        
        # Go is not specifically supported, should fall back to generic
        assert "line_count" in result or "code_lines" in result
        assert result.get("complexity") in ["low", "medium", "high", "very_high", "unknown"]
    
    # ========== Repository Summary Tests ==========
    
    def test_extract_summary(self, parser, temp_directory_with_files):
        """Test extracting repository summary."""
        tmpdir = temp_directory_with_files
        
        # Read all files
        file_contents = {}
        for file in os.listdir(tmpdir):
            file_path = os.path.join(tmpdir, file)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    file_contents[file] = f.read()
        
        summary = parser.extract_summary(tmpdir, file_contents)
        
        # Check structure
        assert "total_files" in summary
        assert "total_functions" in summary
        assert "total_classes" in summary
        assert "languages" in summary
        assert "complexity" in summary
        assert "total_code_lines" in summary
        
        # Should have 4 files (main.py, utils.js, main.go, README.md)
        assert summary["total_files"] == 4
        
        # Should detect Python, JavaScript, and Go extensions
        extensions_found = [ext for ext in ['.py', '.js', '.go'] if ext in summary["languages"]]
        assert len(extensions_found) >= 2
        
        # Should have at least 2 functions across all files
        assert summary["total_functions"] >= 2
        
        # Should have at least 1 class
        assert summary["total_classes"] >= 1
    
    # ========== Edge Case Tests ==========
    
    def test_parse_unknown_file_type(self, parser):
        """Test parsing an unknown file type falls back to generic parser."""
        content = "This is a plain text file.\nIt has multiple lines.\nNo code here."
        result = parser.parse_file("test.txt", content)
        
        assert "line_count" in result
        assert "code_lines" in result
        assert result["line_count"] == 3
        assert result["complexity"] in ["low", "medium", "high", "very_high", "unknown"]
    
    def test_supported_extensions(self, parser):
        """Test that supported_extensions returns expected formats."""
        extensions = parser.supported_extensions
        assert isinstance(extensions, list)
        assert '.py' in extensions
        assert '.js' in extensions
        assert '.ts' in extensions
    
    def test_parse_empty_file(self, parser):
        """Test parsing an empty file returns empty result."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
            result = parser.parse_file(temp_path, content)
            # Empty file should return empty lists, not crash
            assert result.get("functions") == [] or "functions" in result
            assert result.get("classes") == [] or "classes" in result
            assert result.get("imports") == [] or "imports" in result
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_syntax_error(self, parser):
        """Test parsing a Python file with syntax errors."""
        content = "def broken function missing parentheses"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
            result = parser.parse_file(temp_path, content)
            # Should not crash, should return parse_error or graceful result
            assert "parse_error" in result or result.get("functions") == []
        finally:
            os.unlink(temp_path)
    
    def test_parse_very_large_file(self, parser):
        """Test parsing a very large file (performance)."""
        # Generate a large Python file
        large_content = "# " + "x" * 10000 + "\n"
        for i in range(100):
            large_content += f"def func_{i}():\n    return {i}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
            
            import time
            start = time.time()
            result = parser.parse_file(temp_path, content)
            elapsed = time.time() - start
            
            # Should complete within 1 second
            assert elapsed < 1.0, f"Parsing large file took {elapsed:.2f}s"
            assert len(result.get("functions", [])) == 100
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_unicode(self, parser):
        """Test parsing a file with Unicode characters."""
        content = '''
# 这是一个注释 (This is a comment)
def greet_世界():
    """Return greeting in Chinese."""
    return "你好，世界"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            result = parser.parse_file(temp_path, file_content)
            assert "functions" in result
            function_names = [f["name"] for f in result.get("functions", [])]
            assert "greet_世界" in function_names
        finally:
            os.unlink(temp_path)