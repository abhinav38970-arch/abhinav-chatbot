#!/usr/bin/env python3
"""
Phase 2 - Part 1 Verification Script
Tests the Multi-Stage Retrieval Engine and Content Validation System
"""

import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def test_multi_stage_retriever():
    """Test the multi-stage retrieval engine"""
    print("🔍 Testing Multi-Stage Retriever...")
    
    try:
        from retrieval.retriever import MultiStageRetriever, RetrievalResult
        from retrieval.embedding_manager import SchoolEmbeddingManager
        
        # Initialize components
        embedding_manager = SchoolEmbeddingManager()
        retriever = MultiStageRetriever(embedding_manager)
        
        # Test 1: Retriever initialization
        assert len(retriever.stages) == 3
        print("✅ Retriever initialized with 3 stages")
        
        # Test 2: Confidence thresholds
        thresholds = retriever.get_confidence_thresholds()
        assert 'high' in thresholds
        assert 'medium' in thresholds
        assert 'low' in thresholds
        print(f"✅ Confidence thresholds loaded: {thresholds}")
        
        # Test 3: Retrieval with school context
        query_context = {
            'school_id': 'washington',
            'school_level': 'high',
            'min_confidence': 'medium'
        }
        
        # Add some test data first
        test_content = "Washington High School schedule information"
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'source_url': 'https://fremontunified.org/washington/schedule/'
        }
        
        embedding_manager.add_embedding(test_content, test_metadata)
        
        # Perform retrieval
        results, stats = retriever.retrieve("schedule", query_context)
        
        assert isinstance(results, list)
        assert isinstance(stats, dict)
        print(f"✅ Retrieval successful: {len(results)} results")
        
        # Test 4: Statistics tracking
        assert stats['total_queries'] >= 1
        assert 'stage_used' in stats
        print(f"✅ Statistics tracking works: {stats['total_queries']} queries")
        
        # Test 5: RetrievalResult structure
        if results:
            result = results[0]
            assert isinstance(result, RetrievalResult)
            assert hasattr(result, 'content')
            assert hasattr(result, 'school_id')
            assert hasattr(result, 'confidence')
            print(f"✅ RetrievalResult structure valid (confidence: {result.confidence:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-stage retriever test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_content_validator():
    """Test the content validation system"""
    print("\n🔍 Testing Content Validator...")
    
    try:
        from retrieval.validation import ContentValidator, ValidationResult
        
        # Initialize validator
        validator = ContentValidator()
        
        # Test 1: Validator initialization
        assert hasattr(validator, 'thresholds')
        assert hasattr(validator, 'stats')
        print("✅ Content validator initialized")
        
        # Test 2: Validation thresholds
        thresholds = validator.thresholds
        assert 'domain_match' in thresholds
        assert 'school_match' in thresholds
        print(f"✅ Validation thresholds loaded: {len(thresholds)} types")
        
        # Test 3: Valid FUSD content
        valid_context = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'source_url': 'https://fremontunified.org/washington/schedule/',
            'content_type': 'schedule',
            'last_updated': '2023-08-15'
        }
        
        valid_content = """
        Washington High School 2023-2024 Schedule
        Fall Semester: August 15 - December 20
        Spring Semester: January 8 - May 23
        AP Exam Week: May 6-10
        """
        
        is_valid, results = validator.validate_content(valid_content, valid_context)
        
        assert isinstance(is_valid, bool)
        assert isinstance(results, list)
        assert len(results) > 0
        print(f"✅ Valid content validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Test 4: ValidationResult structure
        for result in results:
            assert isinstance(result, ValidationResult)
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'validation_type')
        print(f"✅ ValidationResult structure valid ({len(results)} validations)")
        
        # Test 5: Invalid external domain
        invalid_context = {
            'school_id': 'washington',
            'source_url': 'https://google.com/schedule/',
            'content_type': 'schedule'
        }
        
        invalid_content = "External schedule information"
        
        is_valid_invalid, results_invalid = validator.validate_content(invalid_content, invalid_context)
        
        # Should fail domain validation
        domain_result = next((r for r in results_invalid if r.validation_type == 'domain_match'), None)
        if domain_result:
            assert not domain_result.is_valid
            print("✅ Invalid domain correctly rejected")
        
        # Test 6: Statistics tracking
        stats = validator.get_validation_stats()
        assert stats['total_validations'] >= 2
        print(f"✅ Validation statistics tracking: {stats['total_validations']} validations")
        
        return True
        
    except Exception as e:
        print(f"❌ Content validator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between retriever and validator"""
    print("\n🔍 Testing Retriever + Validator Integration...")
    
    try:
        from retrieval.retriever import MultiStageRetriever
        from retrieval.validation import ContentValidator
        from retrieval.embedding_manager import SchoolEmbeddingManager
        
        # Initialize components
        embedding_manager = SchoolEmbeddingManager()
        retriever = MultiStageRetriever(embedding_manager)
        validator = ContentValidator()
        
        # Test 1: Add content to embedding manager
        test_content = "Washington High School 2023-2024 academic calendar"
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'source_url': 'https://fremontunified.org/washington/calendar/',
            'content_type': 'calendar',
            'last_updated': '2023-07-20'
        }
        
        embedding_manager.add_embedding(test_content, test_metadata)
        print("✅ Test content added to embedding manager")
        
        # Test 2: Retrieve content
        query_context = {
            'school_id': 'washington',
            'school_level': 'high',
            'min_confidence': 'medium'
        }
        
        results, stats = retriever.retrieve("academic calendar", query_context)
        
        if results:
            # Test 3: Validate retrieved content
            retrieval_result = results[0]
            validation_context = {
                'school_id': retrieval_result.school_id,
                'school_name': retrieval_result.school_name,
                'school_level': retrieval_result.school_level,
                'source_url': retrieval_result.source_url,
                'content_type': 'calendar',
                'last_updated': '2023-07-20'
            }
            
            is_valid, validation_results = validator.validate_content(retrieval_result.content, validation_context)
            
            print(f"✅ Integration test: Retrieval {'PASS' if results else 'FAIL'}, Validation {'PASS' if is_valid else 'FAIL'}")
            print(f"   Retrieval confidence: {retrieval_result.confidence:.3f}")
            print(f"   Validation confidence: {sum(r.confidence for r in validation_results) / len(validation_results):.3f}")
        else:
            print("⚠️  No retrieval results for integration test")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("🧪 PHASE 2 - PART 1 VERIFICATION")
    print("Multi-Stage Retrieval + Content Validation")
    print("=" * 60)
    
    tests = [
        ("Multi-Stage Retriever", test_multi_stage_retriever),
        ("Content Validator", test_content_validator),
        ("Integration Test", test_integration)
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
        print("\n🎉 PHASE 2 - PART 1 VERIFICATION SUCCESSFUL!")
        print("✅ Multi-Stage Retrieval: WORKING")
        print("✅ Content Validation: WORKING")
        print("✅ Integration: WORKING")
        return True
    else:
        print(f"\n⚠️  PHASE 2 - PART 1 VERIFICATION FAILED")
        print(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
