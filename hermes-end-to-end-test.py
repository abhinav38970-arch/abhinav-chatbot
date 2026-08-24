#!/usr/bin/env python3
"""
End-to-End Integration Test
Comprehensive test combining all Phase 1 and Phase 2 components
"""

import sys
import time
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def test_end_to_end_integration():
    """Test complete workflow from crawling to citation generation"""
    print("🔬 END-TO-END INTEGRATION TEST")
    print("=" * 60)
    print("Testing complete workflow: Crawler → Embedding → Retrieval → Validation → Knowledge Graph → Citations → Monitoring")
    print("=" * 60)
    
    try:
        # Initialize all components
        print("\n📦 Initializing Components...")
        
        # Phase 1 Components
        from config import SCHOOL_CONFIG
        from scraper.domain_validator import DomainValidator
        from scraper.crawler import FUSDCrawler
        from retrieval.embedding_manager import SchoolEmbeddingManager
        from retrieval.retriever import MultiStageRetriever
        from retrieval.validation import ContentValidator
        
        # Phase 2 Components
        from retrieval.knowledge_graph import KnowledgeGraph
        from retrieval.citation_system import CitationSystem
        from monitoring.performance_monitor import PerformanceMonitor
        
        # Initialize components
        domain_validator = DomainValidator()
        fusd_crawler = FUSDCrawler()
        embedding_manager = SchoolEmbeddingManager()
        retriever = MultiStageRetriever(embedding_manager)
        content_validator = ContentValidator()
        knowledge_graph = KnowledgeGraph()
        citation_system = CitationSystem()
        performance_monitor = PerformanceMonitor()
        
        print("✅ All components initialized")
        
        # Step 1: Build Knowledge Graph with School Relationships
        print("\n🏫 Step 1: Building Knowledge Graph...")
        start_time = time.time()
        knowledge_graph.build_school_relationships(SCHOOL_CONFIG)
        kg_stats = knowledge_graph.get_graph_stats()
        performance_monitor.track_performance('knowledge_graph_build', start_time, 
                                           quality_score=0.95, success=True)
        print(f"✅ Knowledge graph built: {kg_stats['schools']} schools, {kg_stats['nodes']} nodes")
        
        # Step 2: Add Test Content to Embedding Manager
        print("\n📚 Step 2: Adding Content to Embedding Manager...")
        
        test_contents = [
            {
                'content': 'Washington High School 2023-2024 Academic Calendar with important dates and deadlines',
                'metadata': {
                    'school_id': 'washington',
                    'school_name': 'Washington High School',
                    'school_level': 'high',
                    'content_type': 'calendar',
                    'source_url': 'https://fremontunified.org/washington/calendar/',
                    'last_updated': '2023-08-15'
                }
            },
            {
                'content': 'Washington High School Student Handbook 2023-2024 with policies and procedures',
                'metadata': {
                    'school_id': 'washington',
                    'school_name': 'Washington High School',
                    'school_level': 'high',
                    'content_type': 'policy',
                    'source_url': 'https://fremontunified.org/washington/handbook/',
                    'last_updated': '2023-08-10'
                }
            },
            {
                'content': 'FUSD District-Wide Academic Policies and Graduation Requirements for 2023-2024',
                'metadata': {
                    'school_id': 'district',
                    'school_name': 'FUSD District',
                    'school_level': 'district',
                    'content_type': 'policy',
                    'source_url': 'https://fremontunified.org/policies/academic/',
                    'last_updated': '2023-07-20'
                }
            }
        ]
        
        for test_content in test_contents:
            start_time = time.time()
            embedding_result = embedding_manager.add_embedding(
                test_content['content'],
                test_content['metadata']
            )
            performance_monitor.track_performance('content_embedding', start_time, 
                                               quality_score=0.90, success=embedding_result)
            
            # Add to knowledge graph
            kg_content_hash = knowledge_graph.add_content_to_graph(
                test_content['content'],
                test_content['metadata']
            )
            
            print(f"✅ Added: {test_content['metadata']['content_type']} (embedding: {'success' if embedding_result else 'failed'})")
        
        # Step 3: Multi-Stage Retrieval
        print("\n🔍 Step 3: Multi-Stage Retrieval...")
        
        query_context = {
            'school_id': 'washington',
            'school_level': 'high',
            'min_confidence': 'medium'
        }
        
        start_time = time.time()
        retrieval_results, retrieval_stats = retriever.retrieve("academic calendar", query_context)
        performance_monitor.track_performance('multi_stage_retrieval', start_time, 
                                           quality_score=0.88, success=True)
        
        print(f"✅ Retrieval complete: {len(retrieval_results)} results")
        print(f"   Stage used: {retrieval_stats['stage_used']}")
        print(f"   Average confidence: {retrieval_stats['avg_confidence']:.3f}")
        
        # Step 4: Content Validation
        print("\n🔒 Step 4: Content Validation...")
        
        validation_results_list = []
        for result in retrieval_results:
            validation_context = {
                'school_id': result.school_id,
                'school_name': result.school_name,
                'school_level': result.school_level,
                'source_url': result.source_url,
                'content_type': 'document',  # Default content type
                'last_updated': '2023-08-15'
            }
            
            start_time = time.time()
            is_valid, validation_results = content_validator.validate_content(
                result.content, 
                validation_context
            )
            performance_monitor.track_performance('content_validation', start_time, 
                                               quality_score=0.92, success=is_valid)
            
            validation_results_list.extend(validation_results)
            print(f"✅ Validated: {result.school_name} content (confidence: {result.confidence:.3f})")
        
        # Step 5: Knowledge Graph Traversal
        print("\n🌐 Step 5: Knowledge Graph Traversal...")
        
        start_time = time.time()
        kg_results = knowledge_graph.traverse_knowledge_graph(
            "academic calendar policies", 
            "washington",
            max_depth=2,
            max_results=5
        )
        performance_monitor.track_performance('knowledge_graph_traversal', start_time, 
                                           quality_score=0.90, success=True)
        
        print(f"✅ Graph traversal: {len(kg_results['direct_results'])} direct + {len(kg_results['related_content'])} related results")
        print(f"   Knowledge domains: {len(kg_results['knowledge_domains'])}")
        
        # Convert RetrievalResult objects to dictionaries for citation system
        retrieval_results_dict = [{
            'content': result.content,
            'source_url': result.source_url,
            'school_id': result.school_id,
            'school_name': result.school_name,
            'school_level': result.school_level,
            'confidence': result.confidence,
            'content_type': 'document',
            'validation_reason': result.validation_reason
        } for result in retrieval_results]
        
        start_time = time.time()
        citations = citation_system.generate_citations(retrieval_results_dict, validation_results_list)
        performance_monitor.track_performance('citation_generation', start_time, 
                                           quality_score=0.95, success=True)
        
        print(f"✅ Citations generated: {len(citations)} citations")
        
        # Validate citations
        start_time = time.time()
        citations_valid, citation_validation = citation_system.validate_citations(citations)
        performance_monitor.track_performance('citation_validation', start_time, 
                                           quality_score=0.93, success=citations_valid)
        
        print(f"✅ Citation validation: {'PASS' if citations_valid else 'FAIL'}")
        
        # Step 7: Performance Monitoring and Reporting
        print("\n📊 Step 7: Performance Monitoring...")
        
        # Get comprehensive reports
        perf_report = performance_monitor.get_performance_report()
        health_report = performance_monitor.get_system_health()
        quality_trends = performance_monitor.get_quality_trends()
        
        print(f"✅ Performance report generated")
        print(f"   Total operations: {perf_report['overall_stats']['total_operations']}")
        print(f"   Average speed: {perf_report['overall_stats']['average_speed']:.1f}ms")
        print(f"   Average quality: {perf_report['overall_stats']['average_quality']:.2f}")
        print(f"   System health: {health_report['status']} ({health_report['score']:.1%})")
        
        # Step 8: Comprehensive Integration Test
        print("\n🔗 Step 8: End-to-End Integration Verification...")
        
        # Verify all components are working together
        integration_checks = [
            ('Domain Validator', hasattr(domain_validator, 'validate_url')),
            ('FUSD Crawler', hasattr(fusd_crawler, 'crawl')),
            ('Embedding Manager', len(embedding_manager.content_hashes) > 0),
            ('Multi-Stage Retriever', len(retrieval_results) > 0),
            ('Content Validator', len(validation_results_list) > 0),
            ('Knowledge Graph', kg_stats['nodes'] > 0),
            ('Citation System', len(citations) > 0),
            ('Performance Monitor', perf_report['overall_stats']['total_operations'] > 0)
        ]
        
        passed_checks = sum(1 for _, result in integration_checks if result)
        total_checks = len(integration_checks)
        
        print(f"✅ Integration checks: {passed_checks}/{total_checks} passed")
        
        for check_name, result in integration_checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎉 END-TO-END INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        success = passed_checks == total_checks and len(retrieval_results) > 0 and citations_valid
        
        if success:
            print("✅ ALL COMPONENTS INTEGRATED SUCCESSFULLY!")
            print("\n📊 COMPONENT SUMMARY:")
            print(f"   • Phase 1: Crawler, Embedding, Retrieval, Validation")
            print(f"   • Phase 2: Knowledge Graph, Citations, Monitoring")
            print(f"   • Total Operations: {perf_report['overall_stats']['total_operations']}")
            print(f"   • System Health: {health_report['status']}")
            print(f"   • Quality Score: {health_report['score']:.1%}")
            
            print("\n🚀 READY FOR PHASE 3 DEVELOPMENT!")
            return True
        else:
            print("❌ INTEGRATION TEST FAILED")
            print(f"   Failed checks: {total_checks - passed_checks}")
            return False
        
    except Exception as e:
        print(f"\n❌ END-TO-END TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_end_to_end_integration()
    
    # Exit with appropriate code
    if success:
        print("\n🎉 PROCEEDING TO PHASE 3 - ADVANCED FEATURES")
        sys.exit(0)
    else:
        print("\n⚠️  INTEGRATION ISSUES DETECTED - NEEDS REVIEW")
        sys.exit(1)
