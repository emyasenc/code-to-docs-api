# src/services/vector_service.py
"""
Vector service for RAG (Retrieval-Augmented Generation).
Chunks code files, generates embeddings, and retrieves relevant context.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import optional dependencies (don't crash if missing)
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    logger.warning("sentence-transformers not installed. Vector search disabled.")

try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_VECTOR_DB = True
except ImportError:
    HAS_VECTOR_DB = False
    logger.warning("chromadb not installed. Vector DB disabled.")


class VectorService:
    """Service for code chunking, embedding, and retrieval"""
    
    def __init__(self, persist_dir: str = "./data/chroma_db"):
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        if HAS_VECTOR_DB and HAS_EMBEDDINGS:
            self._init_vector_db()
    
    def _init_vector_db(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_dir, exist_ok=True)
            
            # Create client
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            
            # Use sentence-transformers for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create embedding function wrapper
            class CustomEmbeddingFunction(embedding_functions.EmbeddingFunction):
                def __call__(self, texts):
                    return self.embedding_model.encode(texts).tolist()
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection("code_chunks")
            except ValueError:
                self.collection = self.client.create_collection(
                    name="code_chunks",
                    embedding_function=CustomEmbeddingFunction()
                )
            
            logger.info(f"Vector DB initialized at {self.persist_dir}")
        except Exception as e:
            logger.error(f"Vector DB init failed: {e}")
    
    def chunk_code(self, code: str, file_path: str, max_chunk_size: int = 1000) -> List[Dict]:
        """
        Split code into overlapping chunks for embedding.
        
        Args:
            code: The code content
            file_path: Path to the file (for metadata)
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of chunk dicts with 'text', 'start_line', 'end_line', 'file_path'
        """
        chunks = []
        lines = code.split('\n')
        current_chunk = []
        current_length = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_length += len(line)
            
            if current_length >= max_chunk_size or i == len(lines) - 1:
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'file_path': file_path,
                    'start_line': i - len(current_chunk) + 1,
                    'end_line': i,
                    'chunk_id': hashlib.md5(f"{file_path}_{i}".encode()).hexdigest()[:16]
                })
                # Overlap: keep last 20% of lines for next chunk
                overlap_size = max(1, len(current_chunk) // 5)
                current_chunk = current_chunk[-overlap_size:] if overlap_size > 0 else []
                current_length = sum(len(l) for l in current_chunk)
        
        return chunks
    
    def index_repo(self, repo_path: str, file_contents: Dict[str, str]) -> int:
        """
        Index all code files from a repository.
        
        Args:
            repo_path: Path to the repository
            file_contents: Dictionary of {file_path: content}
            
        Returns:
            Number of chunks indexed
        """
        if not self.collection:
            logger.warning("Vector DB not available, skipping indexing")
            return 0
        
        all_chunks = []
        
        for file_path, content in file_contents.items():
            # Only index code files
            if self._is_code_file(file_path):
                try:
                    chunks = self.chunk_code(content, file_path)
                    for chunk in chunks:
                        all_chunks.append(chunk)
                except Exception as e:
                    logger.error(f"Failed to chunk {file_path}: {e}")
        
        if all_chunks:
            try:
                # Delete existing IDs for this repo
                existing_ids = [c['chunk_id'] for c in all_chunks]
                try:
                    self.collection.delete(ids=existing_ids)
                except:
                    pass
                
                # Add new chunks
                self.collection.add(
                    ids=[c['chunk_id'] for c in all_chunks],
                    documents=[c['text'] for c in all_chunks],
                    metadatas=[
                        {'file_path': c['file_path'], 'start_line': c['start_line'], 'end_line': c['end_line']}
                        for c in all_chunks
                    ]
                )
                logger.info(f"Indexed {len(all_chunks)} chunks from {repo_path}")
            except Exception as e:
                logger.error(f"Failed to add chunks to vector DB: {e}")
        
        return len(all_chunks)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant code chunks.
        
        Args:
            query: Search query (e.g., "What does this code do?")
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        if not self.collection:
            logger.warning("Vector DB not available, returning empty results")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            return [
                {
                    'text': doc,
                    'file_path': meta.get('file_path', 'unknown') if meta else 'unknown',
                    'start_line': meta.get('start_line', 0) if meta else 0,
                    'end_line': meta.get('end_line', 0) if meta else 0,
                    'score': 1 - (dist if dist else 0)
                }
                for doc, meta, dist in zip(documents, metadatas, distances)
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file should be indexed (code, not documentation)"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.sql', '.sh', '.bash', '.zsh', '.ps1'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext in code_extensions