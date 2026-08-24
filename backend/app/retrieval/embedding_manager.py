"""
School-Specific Embedding Manager with FAISS Integration

This manager handles:
- School-specific vector indexing
- Global district-wide indexing
- Content deduplication
- School-aware embedding generation
"""

import numpy as np
import hashlib
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.config import SCHOOL_CONFIG

logger = logging.getLogger("embedding_manager")

class SchoolEmbeddingManager:
    """School-specific embedding management with FAISS integration"""
    
    def __init__(self):
        # Initialize embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded: all-MiniLM-L6-v2")
        
        # School-specific and global indices
        self.school_indices = {}  # {school_id: FAISS_index}
        self.global_index = None  # District-wide index
        
        # Deduplication system
        self.content_hashes = set()
        
        logger.info("✅ Embedding manager initialized with school-specific indexing")
        
    def generate_embedding(self, text: str, school_id: Optional[str] = None) -> np.ndarray:
        """Generate embedding with school context"""
        # Add school context to text for better relevance
        if school_id:
            try:
                school = SCHOOL_CONFIG.get_school_by_id(school_id)
                context_text = f"[SCHOOL: {school['school_name']}] {text}"
            except:
                context_text = f"[SCHOOL: {school_id}] {text}"
        else:
            context_text = text
        
        embedding = self.model.encode(context_text)
        return np.array(embedding).astype("float32")
        
    def add_embedding(self, text: str, metadata: Dict) -> bool:
        """Add embedding with school-specific indexing and deduplication"""
        # Generate content hash for deduplication
        content_hash = hashlib.md5(text.encode()).hexdigest()
        
        if content_hash in self.content_hashes:
            logger.debug(f"🔄 DUPLICATE CONTENT: Skipping duplicate text (hash: {content_hash[:8]}...)")
            return False
        
        self.content_hashes.add(content_hash)
        
        # Generate embedding
        school_id = metadata.get('school_id')
        embedding = self.generate_embedding(text, school_id)
        
        # Ensure embedding is 2D array for FAISS
        if isinstance(embedding, np.ndarray) and embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        elif isinstance(embedding, list):
            embedding = np.array(embedding).reshape(1, -1)
        
        # Add to school-specific index
        if school_id:
            if school_id not in self.school_indices:
                # Initialize FAISS index for this school
                self.school_indices[school_id] = self._create_faiss_index()
                logger.info(f"🆕 Created new index for school: {school_id}")
            
            self.school_indices[school_id].add(embedding)
            logger.debug(f"📚 Added to {school_id} index: {text[:50]}...")
        
        # Add to global index
        if not self.global_index:
            self.global_index = self._create_faiss_index()
            logger.info("🆕 Created global district index")
        
        self.global_index.add(embedding)
        logger.debug(f"🌍 Added to global index: {text[:50]}...")
        
        return True
        
    def _create_faiss_index(self):
        """Create a new FAISS index"""
        try:
            import faiss
            dimension = 384  # all-MiniLM-L6-v2 dimension
            return faiss.IndexFlatIP(dimension)
        except ImportError:
            # Fallback for testing without FAISS
            class MockIndex:
                def __init__(self):
                    self.ntotal = 0
                def add(self, embedding):
                    self.ntotal += 1
                def search(self, query, k):
                    # Return mock results
                    scores = [[0.95, 0.90, 0.85, 0.80, 0.75]]
                    indices = [[0, 1, 2, 3, 4]]
                    return (scores, indices)
            return MockIndex()
    
    def search(self, query: str, school_id: Optional[str] = None, k: int = 5) -> List[Dict]:
        """School-aware search with fallback to global index"""
        # Generate query embedding
        query_embedding = self.generate_embedding(query, school_id)
        
        # Ensure query embedding is 2D array for FAISS
        if isinstance(query_embedding, np.ndarray) and query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        elif isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding).reshape(1, -1)
        
        # Try school-specific search first
        if school_id and school_id in self.school_indices:
            try:
                distances, indices = self.school_indices[school_id].search(query_embedding, k)
                results = self._get_results(indices[0], school_id)
                logger.debug(f"🎯 School-specific search: {school_id} ({len(results)} results)")
                return results
            except Exception as e:
                logger.error(f"❌ School-specific search failed: {str(e)}")
        
        # Fallback to global search
        if self.global_index:
            try:
                distances, indices = self.global_index.search(query_embedding, k)
                results = self._get_results(indices[0], "global")
                logger.debug(f"🌍 Global search: ({len(results)} results)")
                return results
            except Exception as e:
                logger.error(f"❌ Global search failed: {str(e)}")
        
        logger.warning("⚠️  No search results found")
        return []
        
    def _get_results(self, indices: List[int], source: str) -> List[Dict]:
        """Convert FAISS indices to result objects"""
        # In a real implementation, this would retrieve the actual documents
        # For now, we'll return placeholder results
        results = []
        for idx in indices:
            if idx != -1:  # Valid result
                results.append({
                    'content': f"Sample content from {source}",
                    'school_id': source if source != "global" else "district",
                    'school_name': source.upper() if source != "global" else "FUSD District",
                    'school_level': 'high' if source == 'washington' else 'district',
                    'source_url': f'https://fremontunified.org/{source}/',
                    'score': 0.95 - (len(results) * 0.05),
                    'metadata': {'source': source, 'index': idx}
                })
        return results
        
    def get_index_stats(self) -> Dict:
        """Get comprehensive index statistics"""
        return {
            'school_indices': len(self.school_indices),
            'global_index_size': getattr(self.global_index, 'ntotal', 0) if self.global_index else 0,
            'school_specific_sizes': {school_id: getattr(idx, 'ntotal', 0) 
                                    for school_id, idx in self.school_indices.items()},
            'total_unique_content': len(self.content_hashes),
            'schools_indexed': list(self.school_indices.keys())
        }
        
    def reset_indices(self):
        """Reset all indices (for testing)"""
        self.school_indices = {}
        self.global_index = None
        self.content_hashes = set()
        logger.info("🔄 All indices reset")

# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = SchoolEmbeddingManager()
    
    # Add some test content
    test_content = "Washington High School schedule information"
    test_metadata = {
        'school_id': 'washington',
        'school_name': 'Washington High School',
        'school_level': 'high'
    }
    
    manager.add_embedding(test_content, test_metadata)
    
    # Search
    results = manager.search("schedule", 'washington', k=3)
    print(f"Search results: {len(results)} found")
    for result in results:
        print(f"  - {result['content']} (score: {result['score']:.3f})")
