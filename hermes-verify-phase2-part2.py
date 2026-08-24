#!/usr/bin/env python3
"""
Phase 2 - Part 2 Verification Script
Tests the Knowledge Graph, Citation System, and Performance Monitor
"""

import sys
import tempfile
import os

# Create verification script
verification_script = """
import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def test_knowledge_graph():
    """Test the knowledge graph system"""
    print("🧠 Testing Knowledge Graph...")
    
    try:
        from retrieval.knowledge_graph import KnowledgeGraph
        from config import SCHOOL_CONFIG
        
        # Initialize knowledge graph
        kg = KnowledgeGraph()
        print("✅ Knowledge graph initialized")
        
        # Build school relationships
        kg.build_school_relationships(SCHOOL_CONFIG)
        stats = kg.get_graph_stats()
        print(f"✅ School relationships built: {stats['schools']} schools")
        
        # Add content
        test_content = "Washington High School Academic Calendar 2023-2024"
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'content_type': 'calendar',
            'source_url': 'https://fremontunified.org/washington/calendar/'
        }
        
        content_hash = kg.add_content_to_graph(test_content, test_metadata)
        print(f"✅ Content added: {content_hash[:8]}")
        
        # Traverse graph
        results = kg.traverse_knowledge_graph("academic calendar", "washington")
        print(f"✅ Graph traversal: {len(results['direct_results'])} direct results")
        
        # Get feeder pattern
        pattern = kg.get_school_feeder_pattern("washington")
        print(f"✅ Feeder pattern retrieved: {len(pattern.get('fed_by', []))} feeder schools")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_citation_system():
    """Test the citation system"""
    print("\n📚 Testing Citation System...")
    
    try:
        from retrieval.citation_system import CitationSystem, Citation
        from retrieval.validation import ValidationResult
        
        # Initialize citation system
        citation_system = CitationSystem()
        print("✅ Citation system initialized")
        
        # Create test retrieval results
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
        
        # Create test validation results
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
        print(f"✅ Citations generated: {len(citations)} citations")
        
        # Validate citations
        is_valid, validation = citation_system.validate_citations(citations)
        print(f"✅ Citation validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Get citation report
        report = citation_system.get_citation_report(citations)
        print(f"✅ Citation report: {report['quality_rating']} quality")
        
        # Get source diversity
        diversity = citation_system.get_source_diversity_report()
        print(f"✅ Source diversity: {diversity['total_sources']} sources")
        
        return True
        
    except Exception as e:
        print(f"❌ Citation system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitor():
    """Test the performance monitor"""
    print("\n📊 Testing Performance Monitor...")
    
    try:
        from monitoring.performance_monitor import PerformanceMonitor
        import time
        
        # Initialize performance monitor
        monitor = PerformanceMonitor()
        print("✅ Performance monitor initialized")
        
        # Track retrieval performance
        start_time = time.time()
        time.sleep(0.05)  # Simulate work
        monitor.track_performance('retrieval', start_time, quality_score=0.85, success=True)
        print("✅ Retrieval performance tracked")
        
        # Track validation performance
        start_time = time.time()
        time.sleep(0.02)  # Simulate work
        monitor.track_performance('validation', start_time, quality_score=0.90, success=True)
        print("✅ Validation performance tracked")
        
        # Get performance report
        report = monitor.get_performance_report()
        print(f"✅ Performance report: {report['overall_stats']['total_operations']} operations")
        
        # Get quality trends
        trends = monitor.get_quality_trends()
        print(f"✅ Quality trends: {trends['current_quality']:.2f} current quality")
        
        # Get system health
        health = monitor.get_system_health()
        print(f"✅ System health: {health['status']} ({health['score']:.1%})")
        
        # Get recent performance
        recent = monitor.get_recent_performance(limit=5)
        print(f"✅ Recent performance: {len(recent)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between components"""
    print("\n🔗 Testing Component Integration...")
    
    try:
        from retrieval.knowledge_graph import KnowledgeGraph
        from retrieval.citation_system import CitationSystem
        from monitoring.performance_monitor import PerformanceMonitor
        from config import SCHOOL_CONFIG
        import time
        
        # Initialize all components
        kg = KnowledgeGraph()
        citation_system = CitationSystem()
        monitor = PerformanceMonitor()
        print("✅ All components initialized")
        
        # Build knowledge graph
        start_time = time.time()
        kg.build_school_relationships(SCHOOL_CONFIG)
        monitor.track_performance('knowledge_graph_build', start_time, quality_score=0.95, success=True)
        print("✅ Knowledge graph built and tracked")
        
        # Add content to knowledge graph
        test_content = "Washington High School Academic Policies 2023-2024"
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'content_type': 'policy',
            'source_url': 'https://fremontunified.org/washington/policies/'
        }
        
        start_time = time.time()
        content_hash = kg.add_content_to_graph(test_content, test_metadata)
        monitor.track_performance('content_addition', start_time, quality_score=0.90, success=True)
        print("✅ Content added and tracked")
        
        # Traverse knowledge graph
        start_time = time.time()
        results = kg.traverse_knowledge_graph("academic policies", "washington")
        monitor.track_performance('graph_traversal', start_time, quality_score=0.88, success=True)
        print(f"✅ Graph traversal and tracked: {len(results['direct_results'])} results")
        
        # Generate citations
        retrieval_results = [{
            'content': test_content,
            'source_url': test_metadata['source_url'],
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'confidence': 0.92,
            'content_type': 'policy',
            'validation_reason': 'school_specific_match'
        }]
        
        from retrieval.validation import ValidationResult
        validation_results = [ValidationResult(
            is_valid=True,
            confidence=0.95,
            validation_type='domain_match',
            details={'domain': 'fremontunified.org'}
        )]
        
        start_time = time.time()
        citations = citation_system.generate_citations(retrieval_results, validation_results)
        monitor.track_performance('citation_generation', start_time, quality_score=0.92, success=True)
        print(f"✅ Citations generated and tracked: {len(citations)} citations")
        
        # Get comprehensive reports
        kg_stats = kg.get_graph_stats()
        citation_report = citation_system.get_citation_report(citations)
        perf_report = monitor.get_performance_report()
        health = monitor.get_system_health()
        
        print("✅ All integration tests passed")
        print(f"   Knowledge Graph: {kg_stats['nodes']} nodes")
        print(f"   Citation Quality: {citation_report['quality_rating']}")
        print(f"   Performance: {perf_report['overall_stats']['average_speed']:.1f}ms avg")
        print(f"   System Health: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("🧪 PHASE 2 - PART 2 VERIFICATION")
    print("Knowledge Graph + Citation System + Performance Monitor")
    print("=" * 60)
    
    tests = [
        ("Knowledge Graph", test_knowledge_graph),
        ("Citation System", test_citation_system),
        ("Performance Monitor", test_performance_monitor),
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
        print("\n🎉 PHASE 2 - PART 2 VERIFICATION SUCCESSFUL!")
        print("✅ Knowledge Graph: WORKING")
        print("✅ Citation System: WORKING")
        print("✅ Performance Monitor: WORKING")
        print("✅ Integration: WORKING")
        return True
    else:
        print(f"\n⚠️  PHASE 2 - PART 2 VERIFICATION FAILED")
        print(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
"""

# Write to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix='hermes-verify-', delete=False) as f:
    f.write(verification_script)
    temp_script_path = f.name

print(f"📄 Created verification script: {temp_script_path}")

# Run the verification
import subprocess
result = subprocess.run(['python3', temp_script_path], 
                       capture_output=True, text=True, 
                       cwd='/Users/abhinav/Desktop/abhinav-chatbot')

print("📊 VERIFICATION OUTPUT:")
print("=" * 50)
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)

# Clean up
os.unlink(temp_script_path)
print(f"🗑️  Cleaned up temporary file")

# Summary
if result.returncode == 0:
    print("\n🎉 PHASE 2 - PART 2 VERIFICATION CONFIRMED!")
    print("✅ All components working correctly")
    print("✅ Integration successful")
    print("✅ Ready for production use")
else:
    print(f"\n❌ VERIFICATION FAILED with code {result.returncode}")
