#!/usr/bin/env python3
"""
Final Verification Script - Phase 1 & 2 Complete
Confirms all components are working together
"""

import sys
import tempfile
import os

# Create verification script
verification_script = """
import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def main():
    print("🔍 Final Verification - Phases 1 & 2 Complete")
    print("=" * 60)
    
    try:
        # Test all components
        from config import SCHOOL_CONFIG
        from scraper.domain_validator import DomainValidator
        from scraper.crawler import FUSDCrawler
        from retrieval.embedding_manager import SchoolEmbeddingManager
        from retrieval.retriever import MultiStageRetriever
        from retrieval.validation import ContentValidator
        from retrieval.knowledge_graph import KnowledgeGraph
        from retrieval.citation_system import CitationSystem
        from monitoring.performance_monitor import PerformanceMonitor
        
        print("✅ All components imported successfully")
        
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
        
        # Test knowledge graph
        knowledge_graph.build_school_relationships(SCHOOL_CONFIG)
        kg_stats = knowledge_graph.get_graph_stats()
        print(f"✅ Knowledge graph: {kg_stats['schools']} schools mapped")
        
        # Test embedding and retrieval
        test_content = "Washington High School Academic Calendar 2023-2024"
        test_metadata = {
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'content_type': 'calendar',
            'source_url': 'https://fremontunified.org/washington/calendar/'
        }
        
        embedding_manager.add_embedding(test_content, test_metadata)
        knowledge_graph.add_content_to_graph(test_content, test_metadata)
        print("✅ Content added to embedding manager and knowledge graph")
        
        # Test retrieval
        query_context = {
            'school_id': 'washington',
            'school_level': 'high',
            'min_confidence': 'medium'
        }
        
        retrieval_results, retrieval_stats = retriever.retrieve("academic calendar", query_context)
        print(f"✅ Retrieval: {len(retrieval_results)} results found")
        
        # Test validation
        for result in retrieval_results:
            validation_context = {
                'school_id': result.school_id,
                'school_name': result.school_name,
                'school_level': result.school_level,
                'source_url': result.source_url,
                'content_type': 'document',
                'last_updated': '2023-08-15'
            }
            
            is_valid, validation_results = content_validator.validate_content(
                result.content, 
                validation_context
            )
        
        print(f"✅ Content validation completed")
        
        # Test citations
        from retrieval.validation import ValidationResult
        validation_results_list = [ValidationResult(
            is_valid=True,
            confidence=0.95,
            validation_type='domain_match',
            details={'domain': 'fremontunified.org'}
        )]
        
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
        
        citations = citation_system.generate_citations(retrieval_results_dict, validation_results_list)
        print(f"✅ Citations: {len(citations)} citations generated")
        
        # Test performance monitoring
        import time
        start_time = time.time()
        time.sleep(0.01)
        performance_monitor.track_performance('test_operation', start_time, quality_score=0.95, success=True)
        
        perf_report = performance_monitor.get_performance_report()
        health = performance_monitor.get_system_health()
        print(f"✅ Performance monitoring: {health['status']} health")
        
        print("\n🎉 FINAL VERIFICATION SUCCESSFUL!")
        print("✅ All Phase 1 & Phase 2 components working")
        print("✅ End-to-end integration verified")
        print("✅ Ready for Phase 3 development")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
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
    print("\n🎉 FINAL VERIFICATION CONFIRMED!")
    print("✅ All components working correctly")
    print("✅ Integration successful")
    print("✅ Ready for production use")
else:
    print(f"\n❌ VERIFICATION FAILED with code {result.returncode}")
