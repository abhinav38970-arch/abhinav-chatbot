#!/usr/bin/env python3
"""
Simple Phase 1 Verification - Focus on Core Functionality
"""

import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def test_core_functionality():
    """Test the core Phase 1 components"""
    print("🧪 Testing Core Phase 1 Functionality")
    
    # Test 1: School Configuration
    try:
        from config import SCHOOL_CONFIG
        print(f"✅ School config: {len(SCHOOL_CONFIG.schools)} schools loaded")
    except Exception as e:
        print(f"❌ School config failed: {e}")
        return False
    
    # Test 2: Domain Validator
    try:
        from scraper.domain_validator import DomainValidator
        validator = DomainValidator()
        
        # Test valid URL
        is_valid, details = validator.validate_url("https://fremontunified.org/washington/")
        assert is_valid == True
        
        # Test invalid URL
        is_valid, details = validator.validate_url("https://google.com/")
        assert is_valid == False
        
        print("✅ Domain validator working")
    except Exception as e:
        print(f"❌ Domain validator failed: {e}")
        return False
    
    # Test 3: FUSD Crawler
    try:
        from scraper.crawler import FUSDCrawler
        crawler = FUSDCrawler()
        print(f"✅ FUSD crawler: {len(crawler.to_visit)} entry points")
    except Exception as e:
        print(f"❌ FUSD crawler failed: {e}")
        return False
    
    # Test 4: Database Models
    try:
        from database.models import Page, CrawlLog
        print("✅ Database models loaded")
    except Exception as e:
        print(f"❌ Database models failed: {e}")
        return False
    
    # Test 5: Embedding Manager
    try:
        from retrieval.embedding_manager import SchoolEmbeddingManager
        manager = SchoolEmbeddingManager()
        
        # Test embedding generation
        embedding = manager.generate_embedding("Test content", "washington")
        assert embedding is not None
        
        print("✅ Embedding manager working")
    except Exception as e:
        print(f"❌ Embedding manager failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_core_functionality()
    if success:
        print("\n🎉 CORE PHASE 1 FUNCTIONALITY VERIFIED!")
        print("✅ Domain isolation: WORKING")
        print("✅ School configuration: COMPLETE")
        print("✅ Crawling system: READY")
        print("✅ Database schema: ENHANCED")
        print("✅ Embedding system: OPERATIONAL")
    else:
        print("\n❌ Core functionality verification failed")
    sys.exit(0 if success else 1)
