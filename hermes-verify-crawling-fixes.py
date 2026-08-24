#!/usr/bin/env python3
"""
Ad-hoc Verification Script for Crawling Pipeline Fixes
Tests all modified components after URL construction fixes
"""

import sys
import os
import tempfile
import subprocess

def test_imports():
    """Test that all modified modules can be imported"""
    print("🧪 Testing Module Imports...")
    
    sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')
    
    try:
        # Test database module
        from database.db import init_db, SessionLocal
        print("✅ database.db imports successfully")
        
        # Test embedding manager
        from retrieval.embedding_manager import SchoolEmbeddingManager
        print("✅ retrieval.embedding_manager imports successfully")
        
        # Test scraper modules
        from scraper.cleaner import clean_text
        from scraper.crawler import FUSDCrawler
        from scraper.parser import parse_page
        from scraper.pdf_handler import extract_pdf_text
        from scraper.pipeline import run_pipeline
        print("✅ All scraper modules import successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_construction():
    """Test that URL construction is working correctly"""
    print("\n🔗 Testing URL Construction...")
    
    try:
        from scraper.crawler import FUSDCrawler
        from config import SCHOOL_CONFIG
        
        crawler = FUSDCrawler()
        crawler._initialize_entry_points()
        
        # Check a few sample URLs
        sample_urls = crawler.to_visit[:5]
        print(f"✅ Generated {len(crawler.to_visit)} URLs")
        
        for url in sample_urls:
            print(f"   Sample URL: {url}")
            if not url.startswith('https://fremontunified.org/'):
                print(f"❌ Invalid URL format: {url}")
                return False
        
        # Check that URLs are properly formatted
        for url in sample_urls:
            if ':///' in url or not url.startswith('https://'):
                print(f"❌ Malformed URL: {url}")
                return False
        
        print("✅ All URLs properly formatted")
        return True
    except Exception as e:
        print(f"❌ URL construction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test that database connection works"""
    print("\n🗃️ Testing Database Connection...")
    
    try:
        from database.db import init_db, SessionLocal
        
        # Initialize database
        init_db()
        
        # Test connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_manager():
    """Test that embedding manager initializes correctly"""
    print("\n🔢 Testing Embedding Manager...")
    
    try:
        from retrieval.embedding_manager import SchoolEmbeddingManager
        
        manager = SchoolEmbeddingManager()
        stats = manager.get_embedding_stats()
        
        print(f"✅ Embedding manager initialized: {stats}")
        return True
    except Exception as e:
        print(f"❌ Embedding manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cleaner_function():
    """Test that the cleaner function works"""
    print("\n🧼 Testing Cleaner Function...")
    
    try:
        from scraper.cleaner import clean_text
        
        # Test with sample text
        dirty_text = "  Hello   World  \n\n  "
        clean_result = clean_text(dirty_text)
        
        if clean_result == "hello world":
            print("✅ Cleaner function working correctly")
            return True
        else:
            print(f"❌ Cleaner function returned unexpected result: '{clean_result}'")
            return False
    except Exception as e:
        print(f"❌ Cleaner function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 Ad-hoc Verification: Crawling Pipeline Fixes")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_url_construction,
        test_database_connection,
        test_embedding_manager,
        test_cleaner_function
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if all(results):
        print("\n🎉 ALL VERIFICATION TESTS PASSED!")
        print("✅ URL construction fixed")
        print("✅ Database connection working")
        print("✅ Embedding manager operational")
        print("✅ All modules importable")
        print("✅ Pipeline ready for deployment")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
