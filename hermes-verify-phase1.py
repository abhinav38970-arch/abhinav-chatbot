#!/usr/bin/env python3
"""
Phase 1 Verification Script
Tests the complete Phase 1 implementation including:
- School configuration loading
- Domain validation
- FUSD crawler initialization
- Database schema
- Vector embedding system
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def test_school_configuration():
    """Test school configuration loading"""
    print("📚 Testing School Configuration...")
    
    try:
        from config import SCHOOL_CONFIG
        
        # Test 1: Configuration loaded
        assert len(SCHOOL_CONFIG.schools) >= 42, f"Expected at least 42 schools, got {len(SCHOOL_CONFIG.schools)}"
        print(f"✅ Loaded {len(SCHOOL_CONFIG.schools)} schools")
        
        # Test 2: All schools have required fields
        required_fields = ['school_id', 'school_name', 'school_level', 'base_urls']
        for school in SCHOOL_CONFIG.schools:
            for field in required_fields:
                assert field in school, f"School {school.get('school_name', 'unknown')} missing {field}"
        print("✅ All schools have required fields")
        
        # Test 3: All URLs are FUSD
        for school in SCHOOL_CONFIG.schools:
            for url in school['base_urls']:
                assert url.startswith('https://fremontunified.org/'), f"Invalid URL: {url}"
        print("✅ All school URLs are FUSD domain")
        
        # Test 4: School levels are valid
        valid_levels = ['high', 'middle', 'elementary', 'preschool', 'alternative', 'adult']
        for school in SCHOOL_CONFIG.schools:
            assert school['school_level'] in valid_levels, f"Invalid level: {school['school_level']}"
        print("✅ All school levels are valid")
        
        # Test 5: Get school by ID
        washington = SCHOOL_CONFIG.get_school_by_id('washington')
        assert washington['school_name'] == 'Washington High School'
        print("✅ School lookup by ID works")
        
        # Test 6: Get schools by level
        high_schools = SCHOOL_CONFIG.get_schools_by_level('high')
        assert len(high_schools) == 5, f"Expected 5 high schools, got {len(high_schools)}"
        print(f"✅ Found {len(high_schools)} high schools")
        
        return True
        
    except Exception as e:
        print(f"❌ School configuration test failed: {str(e)}")
        return False

def test_domain_validation():
    """Test domain validation system"""
    print("\n🔒 Testing Domain Validation...")
    
    try:
        from scraper.domain_validator import DomainValidator
        
        validator = DomainValidator()
        
        # Test 1: Valid FUSD URLs
        valid_urls = [
            "https://fremontunified.org/washington/",
            "https://fremontunified.org/about/",
            "https://fremontunified.org/washington/schedule.pdf"
        ]
        
        for url in valid_urls:
            is_valid, details = validator.validate_url(url)
            assert is_valid, f"Valid URL rejected: {url} - {details['reason']}"
            assert details['domain'] == 'fremontunified.org'
        print(f"✅ {len(valid_urls)} valid FUSD URLs accepted")
        
        # Test 2: Invalid external domains
        invalid_urls = [
            ("https://google.com/", "External domain"),
            ("https://example.com/test", "External domain"),
            ("http://external.site", "External domain")
        ]
        
        for url, expected_reason in invalid_urls:
            is_valid, details = validator.validate_url(url)
            assert not is_valid, f"Invalid URL accepted: {url}"
            assert expected_reason in details['reason']
        print(f"✅ {len(invalid_urls)} external domains blocked")
        
        # Test 3: Blocked file extensions
        blocked_files = [
            ("https://fremontunified.org/test.jpg", "Blocked extension"),
            ("https://fremontunified.org/video.mp4", "Blocked extension"),
            ("https://fremontunified.org/data.zip", "Blocked extension")
        ]
        
        for url, expected_reason in blocked_files:
            is_valid, details = validator.validate_url(url)
            assert not is_valid, f"Blocked file accepted: {url}"
            assert expected_reason in details['reason']
        print(f"✅ {len(blocked_files)} blocked file extensions rejected")
        
        # Test 4: Statistics tracking
        try:
            stats = validator.get_stats()
            print(f"Debug stats: {stats}")  # Debug output
            assert stats['total_checks'] > 0, f"Expected total_checks > 0, got {stats['total_checks']}"
            assert stats['valid_fusd'] > 0, f"Expected valid_fusd > 0, got {stats['valid_fusd']}"
            assert stats['blocked_external'] > 0, f"Expected blocked_external > 0, got {stats['blocked_external']}"
            print("✅ Validation statistics tracking works")
        except AssertionError as e:
            print(f"❌ Statistics assertion failed: {str(e)}")
            print(f"Actual stats: {validator.get_stats()}")
            raise
        
        return True
        
    except Exception as e:
        print(f"❌ Domain validation test failed: {str(e)}")
        return False

def test_crawler_initialization():
    """Test FUSD crawler initialization"""
    print("\n🕷️ Testing FUSD Crawler...")
    
    try:
        from scraper.crawler import FUSDCrawler
        from config import SCHOOL_CONFIG
        
        crawler = FUSDCrawler()
        
        # Test 1: Crawler initialized with entry points
        initial_count = len(crawler.to_visit)
        expected_min = 42  # All schools
        assert initial_count >= expected_min, f"Expected at least {expected_min} entry points, got {initial_count}"
        print(f"✅ Crawler initialized with {initial_count} entry points")
        
        # Test 2: Domain validator integrated
        assert hasattr(crawler, 'validator')
        assert crawler.validator.FUSD_DOMAIN == 'fremontunified.org'
        print("✅ Domain validator integrated")
        
        # Test 3: Crawl rules loaded
        assert hasattr(crawler, 'headers')
        assert 'User-Agent' in crawler.headers
        print("✅ Crawl headers configured")
        
        # Test 4: Statistics tracking
        stats = crawler.get_crawl_stats()
        assert 'pages_crawled' in stats
        assert 'pages_blocked' in stats
        print("✅ Crawl statistics tracking ready")
        
        # Test 5: URL normalization
        test_url = "https://fremontunified.org/washington/"
        normalized = crawler._normalize_url(test_url)
        assert normalized == "https://fremontunified.org/washington"
        print("✅ URL normalization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Crawler initialization test failed: {str(e)}")
        return False

def test_database_schema():
    """Test database schema enhancements"""
    print("\n🗃️ Testing Database Schema...")
    
    try:
        from database.models import Page, CrawlLog
        from sqlalchemy import inspect
        
        # Test 3: Page model has new fields
        page_columns = {col.name for col in Page.__table__.columns}
        required_fields = ['school_id', 'school_name', 'school_level', 'content_hash', 'domain_validated', 'page_metadata']
        
        for field in required_fields:
            assert field in page_columns, f"Missing field in Page: {field}"
        print(f"✅ Page model has all required fields: {', '.join(required_fields)}")
        
        # Test 3: Page model has new fields
        page_columns = {col.name for col in Page.__table__.columns}
        required_fields = ['school_id', 'school_name', 'school_level', 'content_hash', 'domain_validated', 'page_metadata']
        
        for field in required_fields:
            assert field in page_columns, f"Missing field in Page: {field}"
        print(f"✅ Page model has all required fields: {', '.join(required_fields)}")
        
        # Test 3: Indexes configured
        page_indexes = [idx.name for idx in Page.__table__.indexes]
        assert 'idx_school_search' in page_indexes
        assert 'idx_content_hash' in page_indexes
        print("✅ Performance indexes configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {str(e)}")
        return False

def test_embedding_manager():
    """Test vector embedding system"""
    print("\n🎯 Testing Embedding Manager...")
    
    try:
        from retrieval.embedding_manager import SchoolEmbeddingManager
        from config import SCHOOL_CONFIG
        
        manager = SchoolEmbeddingManager()
        
        # Test 1: Manager initialized
        assert hasattr(manager, 'school_indices')
        assert hasattr(manager, 'global_index')
        assert hasattr(manager, 'content_hashes')
        print("✅ Embedding manager initialized")
        
        # Test 2: Embedding generation
        test_text = "Sample content from Washington High School"
        embedding = manager.generate_embedding(test_text, 'washington')
        assert embedding is not None
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        print("✅ Embedding generation works")
        
        # Test 3: Add embedding with deduplication
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high'
        }
        
        # First add should succeed
        result1 = manager.add_embedding(test_text, test_metadata)
        assert result1 == True
        print("✅ First embedding added successfully")
        
        # Duplicate should be rejected
        result2 = manager.add_embedding(test_text, test_metadata)
        assert result2 == False
        print("✅ Duplicate embedding rejected")
        
        # Test 4: Search functionality
        results = manager.search("Washington schedule", 'washington', k=3)
        assert isinstance(results, list)
        print(f"✅ Search returned {len(results)} results")
        
        # Test 5: Statistics
        stats = manager.get_index_stats()
        assert 'school_indices' in stats
        assert 'global_index_size' in stats
        print("✅ Index statistics available")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding manager test failed: {str(e)}")
        return False

def test_pipeline_integration():
    """Test pipeline components integration"""
    print("\n🚀 Testing Pipeline Integration...")
    
    try:
        from scraper.pipeline import extract_school_context_from_url
        from config import SCHOOL_CONFIG
        
        # Test 1: School context extraction
        test_urls = [
            ("https://fremontunified.org/washington/", "washington", "high"),
            ("https://fremontunified.org/kennedy/", "kennedy", "high"),
            ("https://fremontunified.org/about/", "district", "district")
        ]
        
        for url, expected_id, expected_level in test_urls:
            context = extract_school_context_from_url(url)
            assert context['school_id'] == expected_id
            assert context['school_level'] == expected_level
        print(f"✅ School context extraction works for {len(test_urls)} test URLs")
        
        # Test 2: Domain isolation exception
        from scraper.pipeline import DomainIsolationViolation
        try:
            raise DomainIsolationViolation("Test violation")
        except DomainIsolationViolation as e:
            assert str(e) == "Test violation"
        print("✅ Domain isolation exception works")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("🧪 PHASE 1 VERIFICATION - FUSD DOMAIN ISOLATION")
    print("=" * 60)
    
    tests = [
        ("School Configuration", test_school_configuration),
        ("Domain Validation", test_domain_validation),
        ("FUSD Crawler", test_crawler_initialization),
        ("Database Schema", test_database_schema),
        ("Embedding System", test_embedding_manager),
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 PHASE 1 VERIFICATION SUCCESSFUL!")
        print("✅ Domain isolation: PERFECT")
        print("✅ School configuration: COMPLETE")
        print("✅ Crawling system: READY")
        print("✅ Database schema: ENHANCED")
        print("✅ Embedding system: OPERATIONAL")
        return True
    else:
        print(f"\n⚠️  PHASE 1 VERIFICATION FAILED")
        print(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
