"""
Content Validation System

This system validates retrieved content against multiple criteria:
1. Domain/School Metadata Validation
2. Semantic Consistency Validation
3. Recency and Relevance Checks

Features:
- Multi-layer validation gates
- Comprehensive validation tracking
- Confidence-based validation results
- Detailed validation reporting
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

logger = logging.getLogger("content_validator")

@dataclass
class ValidationResult:
    """Structured validation result"""
    is_valid: bool
    confidence: float
    validation_type: str
    details: Optional[Dict] = None
    error_message: Optional[str] = None

class ContentValidator:
    """Multi-layer content validation system"""
    
    def __init__(self):
        # Validation thresholds
        self.thresholds = {
            'domain_match': 0.95,
            'school_match': 0.90,
            'semantic_consistency': 0.85,
            'recency': 0.80,
            'metadata_completeness': 0.75
        }
        
        # Validation statistics
        self.stats = {
            'total_validations': 0,
            'passed': 0,
            'failed': 0,
            'by_type': {},
            'confidence_distribution': {}
        }
        
        # Domain patterns for validation
        self.domain_patterns = {
            'fusd_domain': r'fremontunified\.org',
            'school_url': r'fremontunified\.org/([a-z-]+)/',
            'admin_url': r'fremontunified\.org/(about|policies|contact)/'
        }
        
        # Semantic consistency patterns
        self.semantic_patterns = {
            'school_reference': r'(high school|middle school|elementary school|district)',
            'grade_level': r'(grade|grades|9-12|6-8|K-5|preschool)',
            'academic_term': r'(semester|quarter|trimester|school year|fall|spring|summer)',
            'contact_info': r'(phone|email|address|principal|office)',
            'date_pattern': r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}'
        }
        
    def validate_content(self, content: str, context: Dict) -> Tuple[bool, List[ValidationResult]]:
        """Comprehensive content validation"""
        self.stats['total_validations'] += 1
        
        # Extract validation context
        school_id = context.get('school_id')
        school_level = context.get('school_level')
        source_url = context.get('source_url', '')
        expected_school = context.get('expected_school')
        
        logger.info(f"🔍 Validating content: school={school_id} level={school_level}")
        
        # Run all validation checks
        validation_results = []
        
        # 1. Domain Validation
        domain_result = self._validate_domain(source_url, school_id)
        validation_results.append(domain_result)
        
        # 2. School Metadata Validation
        school_result = self._validate_school_metadata(content, context)
        validation_results.append(school_result)
        
        # 3. Semantic Consistency Validation
        semantic_result = self._validate_semantic_consistency(content, context)
        validation_results.append(semantic_result)
        
        # 4. Recency Validation
        recency_result = self._validate_recency(context)
        validation_results.append(recency_result)
        
        # 5. Metadata Completeness Validation
        metadata_result = self._validate_metadata_completeness(context)
        validation_results.append(metadata_result)
        
        # Calculate overall validation result
        overall_valid = all(result.is_valid for result in validation_results)
        
        # Calculate overall confidence (weighted average)
        confidence_weights = {
            'domain_match': 0.30,
            'school_match': 0.25,
            'semantic_consistency': 0.20,
            'recency': 0.15,
            'metadata_completeness': 0.10
        }
        
        overall_confidence = 0.0
        for result in validation_results:
            weight = confidence_weights.get(result.validation_type, 0.10)
            overall_confidence += result.confidence * weight
        
        # Update statistics
        if overall_valid:
            self.stats['passed'] += 1
        else:
            self.stats['failed'] += 1
        
        # Track by validation type
        for result in validation_results:
            current_count = self.stats['by_type'].get(result.validation_type, 0)
            self.stats['by_type'][result.validation_type] = current_count + 1
        
        # Track confidence distribution
        confidence_bucket = min(int(overall_confidence * 10), 9)
        bucket_key = f"{confidence_bucket * 10}-{(confidence_bucket + 1) * 10}"
        current_count = self.stats['confidence_distribution'].get(bucket_key, 0)
        self.stats['confidence_distribution'][bucket_key] = current_count + 1
        
        logger.info(f"🎯 Validation complete: {'PASS' if overall_valid else 'FAIL'} (confidence: {overall_confidence:.3f})")
        
        return overall_valid, validation_results
        
    def _validate_domain(self, source_url: str, school_id: Optional[str]) -> ValidationResult:
        """Validate domain and URL structure"""
        if not source_url:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type='domain_match',
                error_message='No source URL provided'
            )
        
        # Check if URL matches FUSD domain
        if not re.search(self.domain_patterns['fusd_domain'], source_url):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type='domain_match',
                error_message=f'URL not from FUSD domain: {source_url}'
            )
        
        # Check if URL matches expected school (if school_id provided)
        if school_id:
            school_url_pattern = f'fremontunified\.org/{school_id}/'
            if not re.search(school_url_pattern, source_url):
                # Check if it's a valid FUSD URL but wrong school
                if re.search(self.domain_patterns['school_url'], source_url):
                    return ValidationResult(
                        is_valid=True,  # Still valid FUSD content
                        confidence=0.70,  # Lower confidence for wrong school
                        validation_type='domain_match',
                        details={'expected_school': school_id, 'actual_school': 'other'}
                    )
        
        return ValidationResult(
            is_valid=True,
            confidence=self.thresholds['domain_match'],
            validation_type='domain_match',
            details={'domain': 'fremontunified.org'}
        )
        
    def _validate_school_metadata(self, content: str, context: Dict) -> ValidationResult:
        """Validate school-specific metadata consistency"""
        school_id = context.get('school_id')
        school_name = context.get('school_name')
        school_level = context.get('school_level')
        
        if not school_id:
            return ValidationResult(
                is_valid=True,  # No school context to validate
                confidence=1.0,
                validation_type='school_match',
                details={'reason': 'no_school_context'}
            )
        
        # Check for school name references
        school_name = context.get('school_name', '')
        if school_name:
            school_name_pattern = re.compile(r'\b' + re.escape(school_name) + r'\b', re.IGNORECASE)
            school_id_pattern = re.compile(r'\b' + re.escape(school_id) + r'\b', re.IGNORECASE)
            
            name_match = bool(school_name_pattern.search(content))
            id_match = bool(school_id_pattern.search(content))
        else:
            name_match = False
            id_match = False
        
        # Check for school level references
        level_matches = 0
        if school_level == 'high':
            level_matches += bool(re.search(r'\bhigh school\b|grades? 9-12\b', content, re.IGNORECASE))
        elif school_level == 'middle':
            level_matches += bool(re.search(r'\bmiddle school\b|grades? 6-8\b', content, re.IGNORECASE))
        elif school_level == 'elementary':
            level_matches += bool(re.search(r'\belementary school\b|grades? K-5\b', content, re.IGNORECASE))
        
        # Calculate confidence based on matches
        confidence = 0.5  # Base confidence
        if name_match:
            confidence += 0.25
        if id_match:
            confidence += 0.20
        if level_matches:
            confidence += 0.15
        
        confidence = min(confidence, self.thresholds['school_match'])
        
        is_valid = confidence >= self.thresholds['school_match'] * 0.7  # 70% of threshold
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_type='school_match',
            details={
                'school_name_match': name_match,
                'school_id_match': id_match,
                'school_level_match': bool(level_matches),
                'school_id': school_id,
                'school_name': school_name,
                'school_level': school_level
            }
        )
        
    def _validate_semantic_consistency(self, content: str, context: Dict) -> ValidationResult:
        """Validate semantic consistency of content"""
        school_level = context.get('school_level')
        content_type = context.get('content_type', 'general')
        
        # Calculate semantic consistency score
        semantic_score = 0.5  # Base score
        
        # Check for educational content patterns
        pattern_matches = 0
        total_patterns = len(self.semantic_patterns)
        
        for pattern_name, pattern in self.semantic_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                pattern_matches += 1
        
        pattern_score = pattern_matches / total_patterns
        semantic_score += pattern_score * 0.3
        
        # Check for school-level appropriate content
        level_score = 0.0
        if school_level == 'high':
            # High school content should mention advanced topics
            high_school_patterns = [
                r'AP|Advanced Placement',
                r'college prepar',
                r'SAT|ACT',
                r'graduation requirement'
            ]
            level_matches = sum(1 for pattern in high_school_patterns if re.search(pattern, content, re.IGNORECASE))
            level_score = min(level_matches / len(high_school_patterns), 0.2)
            
        elif school_level == 'middle':
            # Middle school content
            middle_school_patterns = [
                r'electives?',
                r'team|grade level',
                r'transition to high school'
            ]
            level_matches = sum(1 for pattern in middle_school_patterns if re.search(pattern, content, re.IGNORECASE))
            level_score = min(level_matches / len(middle_school_patterns), 0.2)
            
        elif school_level == 'elementary':
            # Elementary school content
            elementary_patterns = [
                r'reading|math|science',
                r'grade [K1-5]',
                r'parent teacher'
            ]
            level_matches = sum(1 for pattern in elementary_patterns if re.search(pattern, content, re.IGNORECASE))
            level_score = min(level_matches / len(elementary_patterns), 0.2)
        
        semantic_score += level_score
        
        # Check for inappropriate content
        inappropriate_patterns = [
            r'\bviolence\b',
            r'\bhate\b',
            r'\bdiscrimination\b',
            r'\bexplicit\b'
        ]
        inappropriate_matches = sum(1 for pattern in inappropriate_patterns if re.search(pattern, content, re.IGNORECASE))
        if inappropriate_matches > 0:
            semantic_score *= 0.5  # Significant penalty
        
        # Calculate final confidence
        confidence = min(semantic_score, self.thresholds['semantic_consistency'])
        is_valid = confidence >= self.thresholds['semantic_consistency'] * 0.8  # 80% of threshold
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_type='semantic_consistency',
            details={
                'semantic_score': semantic_score,
                'pattern_matches': pattern_matches,
                'total_patterns': total_patterns,
                'level_score': level_score,
                'inappropriate_matches': inappropriate_matches
            }
        )
        
    def _validate_recency(self, context: Dict) -> ValidationResult:
        """Validate content recency"""
        last_updated = context.get('last_updated')
        school_year = context.get('school_year')
        is_current = context.get('is_current_year', False)
        
        if not last_updated:
            return ValidationResult(
                is_valid=True,  # No recency info available
                confidence=0.80,
                validation_type='recency',
                details={'reason': 'no_recency_data'}
            )
        
        # Calculate age of content
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated)
            except ValueError:
                return ValidationResult(
                    is_valid=True,
                    confidence=0.75,
                    validation_type='recency',
                    details={'reason': 'invalid_date_format'}
                )
        
        content_age_days = (datetime.now() - last_updated).days
        
        # Calculate recency score
        if content_age_days < 30:  # Very recent
            recency_score = 1.0
        elif content_age_days < 90:  # Recent
            recency_score = 0.9
        elif content_age_days < 180:  # Moderately recent
            recency_score = 0.8
        elif content_age_days < 365:  # Within a year
            recency_score = 0.7
        else:  # Older than a year
            recency_score = 0.6
        
        # Adjust for current school year
        if is_current:
            recency_score = min(recency_score * 1.1, 1.0)
        
        confidence = min(recency_score, self.thresholds['recency'])
        is_valid = confidence >= self.thresholds['recency'] * 0.85  # 85% of threshold
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_type='recency',
            details={
                'content_age_days': content_age_days,
                'is_current_year': is_current,
                'school_year': school_year,
                'recency_score': recency_score
            }
        )
        
    def _validate_metadata_completeness(self, context: Dict) -> ValidationResult:
        """Validate metadata completeness"""
        required_fields = [
            'school_id',
            'school_name',
            'school_level',
            'source_url',
            'content_type'
        ]
        
        optional_fields = [
            'last_updated',
            'school_year',
            'is_current_year',
            'content_hash',
            'author'
        ]
        
        # Check required fields
        missing_required = [field for field in required_fields if field not in context]
        present_required = len(required_fields) - len(missing_required)
        
        # Check optional fields
        present_optional = sum(1 for field in optional_fields if field in context)
        
        # Calculate completeness score
        required_score = present_required / len(required_fields)
        optional_score = present_optional / len(optional_fields)
        
        completeness_score = required_score * 0.7 + optional_score * 0.3
        confidence = min(completeness_score, self.thresholds['metadata_completeness'])
        
        is_valid = confidence >= self.thresholds['metadata_completeness'] * 0.9  # 90% of threshold
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_type='metadata_completeness',
            details={
                'missing_required_fields': missing_required,
                'present_required_fields': present_required,
                'present_optional_fields': present_optional,
                'completeness_score': completeness_score
            }
        )
        
    def get_validation_stats(self) -> Dict:
        """Get comprehensive validation statistics"""
        return {
            'total_validations': self.stats['total_validations'],
            'passed': self.stats['passed'],
            'failed': self.stats['failed'],
            'pass_rate': self.stats['passed'] / self.stats['total_validations'] if self.stats['total_validations'] > 0 else 0,
            'by_type': self.stats['by_type'],
            'confidence_distribution': self.stats['confidence_distribution'],
            'thresholds': self.thresholds.copy()
        }
        
    def set_validation_thresholds(self, thresholds: Dict):
        """Update validation thresholds"""
        self.thresholds.update(thresholds)
        logger.info(f"📊 Updated validation thresholds: {self.thresholds}")
        
    def reset_stats(self):
        """Reset validation statistics"""
        self.stats = {
            'total_validations': 0,
            'passed': 0,
            'failed': 0,
            'by_type': {},
            'confidence_distribution': {}
        }
        logger.info("🔄 Validation statistics reset")
        
    def validate_batch(self, contents: List[str], contexts: List[Dict]) -> Dict:
        """Batch validation for multiple content items"""
        batch_results = []
        
        for content, context in zip(contents, contexts):
            is_valid, validation_results = self.validate_content(content, context)
            batch_results.append({
                'is_valid': is_valid,
                'validation_results': validation_results,
                'context': context
            })
        
        return {
            'batch_results': batch_results,
            'summary': self.get_validation_stats()
        }

# Example usage
if __name__ == "__main__":
    # Initialize validator
    validator = ContentValidator()
    
    # Example validation context
    context = {
        'school_id': 'washington',
        'school_name': 'Washington High School',
        'school_level': 'high',
        'source_url': 'https://fremontunified.org/washington/schedule/',
        'content_type': 'schedule',
        'last_updated': '2023-08-15',
        'school_year': '2023-2024',
        'is_current_year': True
    }
    
    # Example content
    content = """
    Washington High School 2023-2024 Schedule
    
    Fall Semester: August 15 - December 20
    Spring Semester: January 8 - May 23
    
    AP Exam Week: May 6-10
    Graduation: May 25 at 2:00 PM
    
    Contact: (510) 505-7300
    Principal: Bob Moran
    """
    
    # Validate content
    is_valid, results = validator.validate_content(content, context)
    
    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print(f"Validation Details:")
    for result in results:
        print(f"  - {result.validation_type}: {'PASS' if result.is_valid else 'FAIL'} (confidence: {result.confidence:.3f})")
    
    print(f"\nValidation Stats: {validator.get_validation_stats()}")
