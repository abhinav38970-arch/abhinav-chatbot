"""
Enhanced Citation System

This system provides comprehensive citation management with:
- Multi-source tracking
- Confidence-weighted citations
- Source diversity analysis
- Citation validation
- Comprehensive reporting

Features:
- Structured citation generation
- Confidence-based source prioritization
- Cross-school source tracking
- Citation quality validation
- Detailed citation reports
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib
from datetime import datetime
from .validation import ValidationResult  # Import ValidationResult

logger = logging.getLogger("citation_system")

@dataclass
class Citation:
    """Structured citation with confidence and metadata"""
    content_hash: str
    source_url: str
    school_id: str
    school_name: str
    school_level: str
    confidence: float
    relevance_score: float
    content_type: str
    timestamp: str
    metadata: Optional[Dict] = None

class CitationSystem:
    """Advanced citation management system"""
    
    def __init__(self):
        # Confidence thresholds
        self.thresholds = {
            'high_confidence': 0.90,
            'medium_confidence': 0.75,
            'minimum_confidence': 0.60,
            'citation_quality': 0.85
        }
        
        # Citation tracking
        self.citations = []  # All citations
        self.citation_index = {}  # {content_hash: citation}
        self.source_diversity = defaultdict(int)  # {school_id: count}
        
        # Statistics
        self.stats = {
            'total_citations': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'schools_cited': 0,
            'content_types': defaultdict(int),
            'last_updated': None
        }
        
        logger.info("✅ Citation system initialized")
        
    def generate_citations(self, retrieval_results: List[Dict], 
                          validation_results: List[Dict]) -> List[Citation]:
        """Generate structured citations from retrieval and validation results"""
        logger.info(f"📚 Generating citations for {len(retrieval_results)} retrieval results")
        
        citations = []
        
        for retrieval_result in retrieval_results:
            # Extract citation data
            content_hash = self._generate_content_hash(retrieval_result['content'])
            
            # Find corresponding validation results
            validation_result = next(
                (v for v in validation_results 
                 if v.validation_type == 'domain_match' and v.is_valid),
                None
            )
            
            # Calculate confidence (combine retrieval and validation confidence)
            retrieval_confidence = retrieval_result.get('confidence', 0.7)
            validation_confidence = validation_result.confidence if validation_result else 0.8
            
            combined_confidence = (retrieval_confidence * 0.6) + (validation_confidence * 0.4)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(retrieval_result)
            
            # Create citation
            citation = Citation(
                content_hash=content_hash,
                source_url=retrieval_result.get('source_url', 'unknown'),
                school_id=retrieval_result.get('school_id', 'district'),
                school_name=retrieval_result.get('school_name', 'FUSD District'),
                school_level=retrieval_result.get('school_level', 'district'),
                confidence=combined_confidence,
                relevance_score=relevance_score,
                content_type=retrieval_result.get('content_type', 'document'),
                timestamp=datetime.now().isoformat(),
                metadata={
                    'retrieval_confidence': retrieval_confidence,
                    'validation_confidence': validation_confidence,
                    'validation_passed': validation_result.is_valid if validation_result else False,
                    'validation_type': validation_result.validation_type if validation_result else 'none'
                }
            )
            
            citations.append(citation)
            
            # Update tracking
            self._track_citation(citation)
        
        logger.info(f"🎯 Generated {len(citations)} citations")
        
        return citations
        
    def _generate_content_hash(self, content: str) -> str:
        """Generate unique hash for content"""
        return hashlib.md5(content.encode()).hexdigest()
        
    def _calculate_relevance_score(self, retrieval_result: Dict) -> float:
        """Calculate relevance score based on retrieval data"""
        score = 0.5  # Base score
        
        # Add points for high confidence
        confidence = retrieval_result.get('confidence', 0.7)
        if confidence >= 0.9:
            score += 0.3
        elif confidence >= 0.8:
            score += 0.2
        elif confidence >= 0.7:
            score += 0.1
        
        # Add points for school-specific results
        if retrieval_result.get('validation_reason') == 'school_specific_match':
            score += 0.2
        elif retrieval_result.get('validation_reason') == 'school_level_match':
            score += 0.1
        
        # Add points for certain content types
        content_type = retrieval_result.get('content_type', 'document')
        if content_type in ['policy', 'schedule', 'curriculum']:
            score += 0.1
        
        return min(score, 1.0)
        
    def _track_citation(self, citation: Citation) -> None:
        """Track citation statistics"""
        # Add to citation list
        self.citations.append(citation)
        self.citation_index[citation.content_hash] = citation
        
        # Update source diversity
        self.source_diversity[citation.school_id] += 1
        
        # Update statistics
        self.stats['total_citations'] += 1
        
        if citation.confidence >= self.thresholds['high_confidence']:
            self.stats['high_confidence'] += 1
        elif citation.confidence >= self.thresholds['medium_confidence']:
            self.stats['medium_confidence'] += 1
        else:
            self.stats['low_confidence'] += 1
        
        # Track content types
        self.stats['content_types'][citation.content_type] += 1
        
        # Update school count
        self.stats['schools_cited'] = len(self.source_diversity)
        
        self.stats['last_updated'] = datetime.now().isoformat()
        
    def validate_citations(self, citations: List[Citation]) -> Tuple[bool, List[Dict]]:
        """Validate citation quality and consistency"""
        logger.info(f"🔍 Validating {len(citations)} citations")
        
        validation_results = []
        overall_valid = True
        
        for citation in citations:
            # Check minimum confidence
            if citation.confidence < self.thresholds['minimum_confidence']:
                validation_results.append({
                    'citation_hash': citation.content_hash,
                    'is_valid': False,
                    'reason': 'low_confidence',
                    'confidence': citation.confidence,
                    'threshold': self.thresholds['minimum_confidence']
                })
                overall_valid = False
                continue
            
            # Check source URL validity
            if not citation.source_url or not citation.source_url.startswith('https://fremontunified.org/'):
                validation_results.append({
                    'citation_hash': citation.content_hash,
                    'is_valid': False,
                    'reason': 'invalid_source_url',
                    'source_url': citation.source_url
                })
                overall_valid = False
                continue
            
            # Check school consistency
            if citation.school_id == 'district' and citation.school_level != 'district':
                validation_results.append({
                    'citation_hash': citation.content_hash,
                    'is_valid': False,
                    'reason': 'school_level_mismatch',
                    'school_id': citation.school_id,
                    'school_level': citation.school_level
                })
                overall_valid = False
                continue
            
            # All checks passed
            validation_results.append({
                'citation_hash': citation.content_hash,
                'is_valid': True,
                'reason': 'all_checks_passed',
                'confidence': citation.confidence,
                'relevance': citation.relevance_score
            })
        
        logger.info(f"🎯 Citation validation: {'PASS' if overall_valid else 'FAIL'}")
        
        return overall_valid, validation_results
        
    def get_citation_report(self, citations: Optional[List[Citation]] = None) -> Dict:
        """Generate comprehensive citation report"""
        citations_to_analyze = citations if citations else self.citations
        
        if not citations_to_analyze:
            return {'error': 'No citations to analyze'}
        
        # Calculate statistics
        total_citations = len(citations_to_analyze)
        
        # Confidence distribution
        high_conf = sum(1 for c in citations_to_analyze if c.confidence >= self.thresholds['high_confidence'])
        med_conf = sum(1 for c in citations_to_analyze 
                      if self.thresholds['medium_confidence'] <= c.confidence < self.thresholds['high_confidence'])
        low_conf = sum(1 for c in citations_to_analyze if c.confidence < self.thresholds['medium_confidence'])
        
        # School diversity
        schools = set(c.school_id for c in citations_to_analyze)
        school_distribution = {school: sum(1 for c in citations_to_analyze if c.school_id == school) 
                             for school in schools}
        
        # Content type distribution
        content_types = set(c.content_type for c in citations_to_analyze)
        content_type_distribution = {ct: sum(1 for c in citations_to_analyze if c.content_type == ct) 
                                   for ct in content_types}
        
        # Average confidence and relevance
        avg_confidence = sum(c.confidence for c in citations_to_analyze) / total_citations
        avg_relevance = sum(c.relevance_score for c in citations_to_analyze) / total_citations
        
        # Quality score (0-1)
        quality_score = (avg_confidence * 0.6) + (avg_relevance * 0.4)
        
        return {
            'total_citations': total_citations,
            'confidence_distribution': {
                'high': high_conf,
                'medium': med_conf,
                'low': low_conf,
                'high_percentage': high_conf / total_citations if total_citations > 0 else 0,
                'medium_percentage': med_conf / total_citations if total_citations > 0 else 0,
                'low_percentage': low_conf / total_citations if total_citations > 0 else 0
            },
            'school_diversity': {
                'total_schools': len(schools),
                'distribution': school_distribution,
                'diversity_score': min(len(schools) / 5, 1.0)  # Normalized to 0-1
            },
            'content_type_distribution': content_type_distribution,
            'average_confidence': avg_confidence,
            'average_relevance': avg_relevance,
            'quality_score': quality_score,
            'quality_rating': self._get_quality_rating(quality_score),
            'timestamp': datetime.now().isoformat()
        }
        
    def _get_quality_rating(self, quality_score: float) -> str:
        """Get human-readable quality rating"""
        if quality_score >= 0.9:
            return 'excellent'
        elif quality_score >= 0.8:
            return 'very_good'
        elif quality_score >= 0.7:
            return 'good'
        elif quality_score >= 0.6:
            return 'fair'
        else:
            return 'poor'
        
    def filter_citations_by_confidence(self, citations: List[Citation], 
                                      min_confidence: str = 'medium') -> List[Citation]:
        """Filter citations by confidence level"""
        threshold = self.thresholds.get(min_confidence, self.thresholds['medium_confidence'])
        
        return [c for c in citations if c.confidence >= threshold]
        
    def get_top_citations(self, citations: List[Citation], 
                         top_n: int = 5) -> List[Citation]:
        """Get top citations by combined score"""
        # Sort by combined score (confidence + relevance)
        scored_citations = [
            (c, c.confidence * 0.7 + c.relevance_score * 0.3) 
            for c in citations
        ]
        
        # Sort by score descending
        scored_citations.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return [c[0] for c in scored_citations[:top_n]]
        
    def get_citation_by_hash(self, content_hash: str) -> Optional[Citation]:
        """Get citation by content hash"""
        return self.citation_index.get(content_hash)
        
    def get_source_diversity_report(self) -> Dict:
        """Get source diversity analysis"""
        if not self.source_diversity:
            return {'error': 'No citations tracked'}
        
        total_citations = sum(self.source_diversity.values())
        
        return {
            'total_sources': len(self.source_diversity),
            'total_citations': total_citations,
            'distribution': dict(self.source_diversity),
            'percentages': {school: (count / total_citations) 
                          for school, count in self.source_diversity.items()},
            'diversity_score': min(len(self.source_diversity) / 5, 1.0),
            'dominant_source': max(self.source_diversity.items(), key=lambda x: x[1])[0]
        }
        
    def reset_citations(self) -> None:
        """Reset citation tracking"""
        self.citations = []
        self.citation_index = {}
        self.source_diversity = defaultdict(int)
        self.stats = {
            'total_citations': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'schools_cited': 0,
            'content_types': defaultdict(int),
            'last_updated': None
        }
        logger.info("🔄 Citation system reset")
        
    def export_citations(self, citations: Optional[List[Citation]] = None) -> List[Dict]:
        """Export citations as dictionaries"""
        citations_to_export = citations if citations else self.citations
        
        return [{
            'content_hash': c.content_hash,
            'source_url': c.source_url,
            'school_id': c.school_id,
            'school_name': c.school_name,
            'school_level': c.school_level,
            'confidence': c.confidence,
            'relevance_score': c.relevance_score,
            'content_type': c.content_type,
            'timestamp': c.timestamp,
            'metadata': c.metadata
        } for c in citations_to_export]

# Example usage
if __name__ == "__main__":
    # Initialize citation system
    citation_system = CitationSystem()
    
    # Example retrieval results (simplified)
    retrieval_results = [
        {
            'content': 'Washington High School 2023-2024 Calendar',
            'source_url': 'https://fremontunified.org/washington/calendar/',
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'confidence': 0.92,
            'content_type': 'calendar',
            'validation_reason': 'school_specific_match'
        }
    ]
    
    # Example validation results
    validation_results = [
        ValidationResult(
            is_valid=True,
            confidence=0.95,
            validation_type='domain_match',
            details={'domain': 'fremontunified.org'}
        )
    ]
    
    # Generate citations
    citations = citation_system.generate_citations(retrieval_results, validation_results)
    
    print(f"Generated {len(citations)} citations")
    for citation in citations:
        print(f"  - {citation.school_name}: {citation.confidence:.2f} confidence")
    
    # Get citation report
    report = citation_system.get_citation_report(citations)
    print(f"Citation quality: {report['quality_rating']} ({report['quality_score']:.2f})")
