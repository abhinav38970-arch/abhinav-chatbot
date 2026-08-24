#!/usr/bin/env python3
"""
Simple Phase 2 - Part 2 Verification
"""

import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def main():
    print("🧪 Phase 2 - Part 2 Verification")
    print("=" * 50)
    
    try:
        # Test 1: Knowledge Graph
        from retrieval.knowledge_graph import KnowledgeGraph
        from config import SCHOOL_CONFIG
        
        kg = KnowledgeGraph()
        kg.build_school_relationships(SCHOOL_CONFIG)
        stats = kg.get_graph_stats()
        print(f"✅ Knowledge Graph: {stats['schools']} schools mapped")
        
        # Test 2: Citation System
        from retrieval.citation_system import CitationSystem
        from retrieval.validation import ValidationResult
        
        citation_system = CitationSystem()
        
        retrieval_results = [{
            'content': 'Test content',
            'source_url': 'https://fremontunified.org/washington/',
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'confidence': 0.92,
            'content_type': 'document',
            'validation_reason': 'school_specific_match'
        }]
        
        validation_results = [ValidationResult(
            is_valid=True,
            confidence=0.95,
            validation_type='domain_match',
            details={'domain': 'fremontunified.org'}
        )]
        
        citations = citation_system.generate_citations(retrieval_results, validation_results)
        print(f"✅ Citation System: {len(citations)} citations generated")
        
        # Test 3: Performance Monitor
        from monitoring.performance_monitor import PerformanceMonitor
        import time
        
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        time.sleep(0.05)
        monitor.track_performance('test_operation', start_time, quality_score=0.90, success=True)
        
        report = monitor.get_performance_report()
        print(f"✅ Performance Monitor: {report['overall_stats']['total_operations']} operations tracked")
        
        # Test 4: Integration
        content_hash = kg.add_content_to_graph("Test content", {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'content_type': 'document'
        })
        
        results = kg.traverse_knowledge_graph("test", "washington")
        health = monitor.get_system_health()
        
        print(f"✅ Integration: All components working together")
        print(f"   Graph: {len(results['direct_results'])} results")
        print(f"   Health: {health['status']}")
        
        print("\n🎉 PHASE 2 - PART 2 VERIFICATION SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
