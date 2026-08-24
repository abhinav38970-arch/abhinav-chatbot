"""
Multi-Stage Retrieval Engine with Confidence-Based Routing

This engine implements a hierarchical retrieval system:
1. School-specific search (highest priority)
2. School-level search (middle/high/elementary)
3. District-wide search (fallback)

Features:
- Confidence-based routing between stages
- Validation gates at each retrieval level
- Comprehensive logging and statistics
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from backend.app.config import SCHOOL_CONFIG
from backend.app.retrieval.embedding_manager import SchoolEmbeddingManager

logger = logging.getLogger("multi_stage_retriever")

@dataclass
class RetrievalResult:
    """Structured retrieval result with confidence and metadata"""
    content: str
    school_id: str
    school_name: str
    school_level: str
    source_url: str
    confidence: float
    validation_passed: bool
    validation_reason: Optional[str] = None
    metadata: Optional[Dict] = None

class RetrievalStage:
    """Base class for retrieval stages"""
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.hits = 0
        self.misses = 0
        
    def search(self, query: str, query_context: Dict) -> List[RetrievalResult]:
        """Search implementation for this stage"""
        raise NotImplementedError
        
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'stage': self.name,
            'priority': self.priority,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }

class SchoolSpecificStage(RetrievalStage):
    """Stage 1: School-specific retrieval (highest priority)"""
    def __init__(self, embedding_manager: SchoolEmbeddingManager):
        super().__init__("school_specific", 1)
        self.embedding_manager = embedding_manager
        
    def search(self, query: str, query_context: Dict) -> List[RetrievalResult]:
        """Search within specific school context"""
        school_id = query_context.get('school_id')
        
        if not school_id:
            self.misses += 1
            return []
        
        # Get school information
        school = SCHOOL_CONFIG.get_school_by_id(school_id)
        if not school:
            self.misses += 1
            return []
        
        # Search in school-specific index
        results = self.embedding_manager.search(query, school_id, k=5)
        
        if not results:
            self.misses += 1
            return []
        
        # Convert to RetrievalResult format
        retrieval_results = []
        for result in results:
            retrieval_results.append(RetrievalResult(
                content=result['content'],
                school_id=school_id,
                school_name=school['school_name'],
                school_level=school['school_level'],
                source_url=result.get('source_url', 'unknown'),
                confidence=result['score'],
                validation_passed=True,
                validation_reason="school_specific_match",
                metadata=result.get('metadata')
            ))
        
        self.hits += 1
        logger.info(f"🎯 School-specific hit: {school_id} ({len(retrieval_results)} results)")
        
        return retrieval_results

class SchoolLevelStage(RetrievalStage):
    """Stage 2: School level retrieval (middle/high/elementary)"""
    def __init__(self, embedding_manager: SchoolEmbeddingManager):
        super().__init__("school_level", 2)
        self.embedding_manager = embedding_manager
        
    def search(self, query: str, query_context: Dict) -> List[RetrievalResult]:
        """Search within school level context"""
        school_level = query_context.get('school_level')
        
        if not school_level:
            self.misses += 1
            return []
        
        # Get all schools at this level
        schools_at_level = SCHOOL_CONFIG.get_schools_by_level(school_level)
        if not schools_at_level:
            self.misses += 1
            return []
        
        # Search across all schools at this level
        all_results = []
        for school in schools_at_level:
            school_id = school['school_id']
            results = self.embedding_manager.search(query, school_id, k=3)
            
            for result in results:
                all_results.append(RetrievalResult(
                    content=result['content'],
                    school_id=school_id,
                    school_name=school['school_name'],
                    school_level=school_level,
                    source_url=result.get('source_url', 'unknown'),
                    confidence=result['score'] * 0.9,  # Slightly lower confidence
                    validation_passed=True,
                    validation_reason="school_level_match",
                    metadata=result.get('metadata')
                ))
        
        if not all_results:
            self.misses += 1
            return []
        
        # Sort by confidence and limit to top 5
        all_results.sort(key=lambda x: x.confidence, reverse=True)
        top_results = all_results[:5]
        
        self.hits += 1
        logger.info(f"🎓 School-level hit: {school_level} ({len(top_results)} results)")
        
        return top_results

class DistrictWideStage(RetrievalStage):
    """Stage 3: District-wide retrieval (fallback)"""
    def __init__(self, embedding_manager: SchoolEmbeddingManager):
        super().__init__("district_wide", 3)
        self.embedding_manager = embedding_manager
        
    def search(self, query: str, query_context: Dict) -> List[RetrievalResult]:
        """Search across entire district"""
        # Search in global index
        results = self.embedding_manager.search(query, None, k=8)  # None = global search
        
        if not results:
            self.misses += 1
            return []
        
        # Convert to RetrievalResult format
        retrieval_results = []
        for result in results:
            retrieval_results.append(RetrievalResult(
                content=result['content'],
                school_id=result.get('school_id', 'district'),
                school_name=result.get('school_name', 'FUSD District'),
                school_level=result.get('school_level', 'district'),
                source_url=result.get('source_url', 'unknown'),
                confidence=result['score'] * 0.8,  # Lower confidence for district
                validation_passed=True,
                validation_reason="district_match",
                metadata=result.get('metadata')
            ))
        
        self.hits += 1
        logger.info(f"🏛️ District-wide hit: ({len(retrieval_results)} results)")
        
        return retrieval_results

class MultiStageRetriever:
    """Hierarchical retrieval engine with confidence-based routing"""
    
    def __init__(self, embedding_manager: SchoolEmbeddingManager):
        self.embedding_manager = embedding_manager
        
        # Initialize retrieval stages
        self.stages = [
            SchoolSpecificStage(embedding_manager),
            SchoolLevelStage(embedding_manager),
            DistrictWideStage(embedding_manager)
        ]
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'high': 0.85,      # School-specific required
            'medium': 0.70,    # School-level acceptable
            'low': 0.55,       # District-wide minimum
            'fallback': 0.40   # Absolute minimum
        }
        
        self.stats = {
            'total_queries': 0,
            'school_hits': 0,
            'level_hits': 0,
            'district_hits': 0,
            'no_results': 0,
            'avg_confidence': 0,
            'confidence_distribution': {}
        }
        
    def retrieve(self, query: str, query_context: Dict) -> Tuple[List[RetrievalResult], Dict]:
        """Multi-stage retrieval with confidence-based routing"""
        self.stats['total_queries'] += 1
        
        # Extract query context
        school_id = query_context.get('school_id')
        school_level = query_context.get('school_level')
        min_confidence = query_context.get('min_confidence', 'medium')
        
        logger.info(f"🔍 Retrieval started: query='{query[:50]}...' school={school_id} level={school_level}")
        
        # Stage 1: School-specific search (highest priority)
        results = []
        stage_used = None
        
        if school_id:
            school_results = self.stages[0].search(query, query_context)
            if school_results:
                results = school_results
                stage_used = "school_specific"
                self.stats['school_hits'] += 1
                logger.info(f"✅ Stage 1 hit: {len(results)} results from {school_id}")
        
        # Stage 2: School-level search (fallback if no school results or low confidence)
        if not results or (results and max(r.confidence for r in results) < self.confidence_thresholds['high']):
            level_results = self.stages[1].search(query, query_context)
            if level_results:
                # Combine results (prioritize school results if they exist)
                if results:
                    # Filter low-confidence school results
                    high_confidence_school = [r for r in results if r.confidence >= self.confidence_thresholds['high']]
                    if high_confidence_school:
                        results = high_confidence_school
                    else:
                        results = level_results
                        stage_used = "school_level"
                else:
                    results = level_results
                    stage_used = "school_level"
                
                self.stats['level_hits'] += 1
                logger.info(f"✅ Stage 2 hit: {len(results)} results from {school_level} level")
        
        # Stage 3: District-wide search (final fallback)
        if not results or (results and max(r.confidence for r in results) < self.confidence_thresholds['medium']):
            district_results = self.stages[2].search(query, query_context)
            if district_results:
                # Apply minimum confidence filter
                confidence_threshold = self.confidence_thresholds.get(min_confidence, self.confidence_thresholds['low'])
                filtered_results = [r for r in district_results if r.confidence >= confidence_threshold]
                
                if filtered_results:
                    results = filtered_results
                    stage_used = "district_wide"
                    self.stats['district_hits'] += 1
                    logger.info(f"✅ Stage 3 hit: {len(results)} results from district")
                else:
                    logger.info(f"⚠️  District results below confidence threshold ({confidence_threshold})")
        
        # Final validation
        if not results:
            self.stats['no_results'] += 1
            logger.warning(f"❌ No results found for query: '{query[:50]}...'")
            return [], self._get_retrieval_stats(stage_used)
        
        # Update statistics
        avg_confidence = sum(r.confidence for r in results) / len(results)
        self.stats['avg_confidence'] = (
            (self.stats['avg_confidence'] * (self.stats['total_queries'] - 1) + avg_confidence) 
            / self.stats['total_queries']
        )
        
        # Track confidence distribution
        for result in results:
            confidence_bucket = min(int(result.confidence * 10), 9)  # 0-9 buckets
            bucket_key = f"{confidence_bucket * 10}-{(confidence_bucket + 1) * 10}"
            current_count = self.stats['confidence_distribution'].get(bucket_key, 0)
            self.stats['confidence_distribution'][bucket_key] = current_count + 1
        
        logger.info(f"🎯 Retrieval complete: {len(results)} results (avg confidence: {avg_confidence:.3f})")
        
        return results, self._get_retrieval_stats(stage_used)
        
    def _get_retrieval_stats(self, stage_used: Optional[str]) -> Dict:
        """Get comprehensive retrieval statistics"""
        stage_stats = {stage.name: stage.get_stats() for stage in self.stages}
        
        return {
            'stage_used': stage_used,
            'total_queries': self.stats['total_queries'],
            'school_hits': self.stats['school_hits'],
            'level_hits': self.stats['level_hits'],
            'district_hits': self.stats['district_hits'],
            'no_results': self.stats['no_results'],
            'avg_confidence': self.stats['avg_confidence'],
            'confidence_distribution': self.stats['confidence_distribution'],
            'stage_details': stage_stats,
            'hit_rates': {
                'school_hit_rate': self.stats['school_hits'] / self.stats['total_queries'] if self.stats['total_queries'] > 0 else 0,
                'level_hit_rate': self.stats['level_hits'] / self.stats['total_queries'] if self.stats['total_queries'] > 0 else 0,
                'district_hit_rate': self.stats['district_hits'] / self.stats['total_queries'] if self.stats['total_queries'] > 0 else 0
            }
        }
        
    def get_confidence_thresholds(self) -> Dict:
        """Get current confidence thresholds"""
        return self.confidence_thresholds.copy()
        
    def set_confidence_thresholds(self, thresholds: Dict):
        """Update confidence thresholds"""
        self.confidence_thresholds.update(thresholds)
        logger.info(f"📊 Updated confidence thresholds: {self.confidence_thresholds}")
        
    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'total_queries': 0,
            'school_hits': 0,
            'level_hits': 0,
            'district_hits': 0,
            'no_results': 0,
            'avg_confidence': 0,
            'confidence_distribution': {}
        }
        for stage in self.stages:
            stage.hits = 0
            stage.misses = 0
        logger.info("🔄 Statistics reset")

# Example usage
if __name__ == "__main__":
    # This would be used in the main application
    from backend.app.retrieval.embedding_manager import SchoolEmbeddingManager
    
    # Initialize components
    embedding_manager = SchoolEmbeddingManager()
    retriever = MultiStageRetriever(embedding_manager)
    
    # Example query
    query_context = {
        'school_id': 'washington',
        'school_level': 'high',
        'min_confidence': 'medium'
    }
    
    results, stats = retriever.retrieve("school schedule", query_context)
    print(f"Retrieved {len(results)} results")
    print(f"Stats: {stats}")
