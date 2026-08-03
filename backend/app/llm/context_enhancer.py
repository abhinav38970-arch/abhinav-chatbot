from backend.app.scraper.year_detector import SchoolYearDetector
from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from datetime import datetime
import json

class LLMContextEnhancer:
    """
    Enhances LLM prompts with temporal context and relevance information
    """
    
    def __init__(self):
        self.year_detector = SchoolYearDetector()
        self.current_year = self.year_detector.get_current_school_year()
    
    def get_temporal_context(self) -> dict:
        """
        Generate temporal context for LLM prompts
        """
        return {
            "current_school_year": self.current_year,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "current_month": datetime.now().strftime("%B"),
            "academic_period": self._get_academic_period(),
            "temporal_guidance": self._get_temporal_guidance()
        }
    
    def _get_academic_period(self) -> str:
        """
        Determine where we are in the academic year
        """
        month = datetime.now().month
        
        if month >= 8 and month <= 10:
            return "Fall Semester - Beginning of School Year"
        elif month >= 11 or month <= 1:
            return "Fall Semester - Mid Year"
        elif month >= 2 and month <= 4:
            return "Spring Semester - Mid Year"
        elif month >= 5 and month <= 7:
            return "Spring Semester - End of School Year"
        else:
            return "Summer Break"
    
    def _get_temporal_guidance(self) -> str:
        """
        Generate natural language guidance about temporal relevance
        """
        return f"""
Current Context: We are in the {self.current_year} school year. 
When answering questions, prioritize information relevant to the current academic year.
If information from previous years (like 2025-2026 or earlier) is mentioned, clearly indicate it's outdated.
Always check dates and school year references in the source material before providing answers.
"""
    
    def enhance_prompt(self, original_prompt: str, search_results: list = None) -> str:
        """
        Enhance the original prompt with temporal context and relevance information
        """
        temporal_context = self.get_temporal_context()
        
        enhanced_prompt = f"""Temporal Context:
{temporal_context['temporal_guidance']}

Current School Year: {temporal_context['current_school_year']}
Current Date: {temporal_context['current_date']}
Academic Period: {temporal_context['academic_period']}

Original Question: {original_prompt}
"""
        
        if search_results:
            enhanced_prompt += f"\n\nRelevant Information (with recency scores):\n"
            for i, result in enumerate(search_results, 1):
                recency_info = f" (Recency: {result.get('recency_score', 0.5):.2f})"
                if result.get('school_year') != self.current_year:
                    recency_info += f" [OUTDATED: {result.get('school_year', 'Unknown year')}]"
                enhanced_prompt += f"\n{i}. {result.get('content', '')[:200]}...{recency_info}\n"
        
        enhanced_prompt += f"\n\nPlease provide a comprehensive answer, giving priority to current {self.current_year} information."
        
        return enhanced_prompt
    
    def get_relevant_pages(self, query: str, limit: int = 5) -> list:
        """
        Get most relevant pages from database with recency scoring
        """
        db = SessionLocal()
        try:
            # Query pages, ordered by recency score and current year flag
            pages = (db.query(Page)
                    .filter(Page.content.contains(query) | Page.url.contains(query))
                    .order_by(Page.recency_score.desc(), Page.is_current_year.desc())
                    .limit(limit)
                    .all())
            
            results = []
            for page in pages:
                results.append({
                    'url': page.url,
                    'content': page.content,
                    'school_year': page.school_year,
                    'recency_score': page.recency_score,
                    'is_current_year': bool(page.is_current_year),
                    'last_updated': page.last_updated.strftime('%Y-%m-%d') if page.last_updated else None
                })
            
            return results
            
        finally:
            db.close()
    
    def create_knowledge_context(self, question: str) -> dict:
        """
        Create a comprehensive knowledge context for the LLM
        """
        # Get relevant pages from database
        relevant_pages = self.get_relevant_pages(question)
        
        # Generate temporal context
        temporal_context = self.get_temporal_context()
        
        return {
            'question': question,
            'temporal_context': temporal_context,
            'relevant_pages': relevant_pages,
            'knowledge_graph': self._build_knowledge_graph(relevant_pages),
            'priority_guidance': self._generate_priority_guidance(relevant_pages)
        }
    
    def _build_knowledge_graph(self, pages: list) -> dict:
        """
        Build a simple knowledge graph from relevant pages
        """
        graph = {
            'current_year_nodes': [],
            'outdated_nodes': [],
            'relationships': []
        }
        
        for page in pages:
            node = {
                'url': page['url'],
                'school_year': page['school_year'],
                'recency_score': page['recency_score']
            }
            
            if page['is_current_year']:
                graph['current_year_nodes'].append(node)
            else:
                graph['outdated_nodes'].append(node)
        
        return graph
    
    def _generate_priority_guidance(self, pages: list) -> str:
        """
        Generate guidance on which sources to prioritize
        """
        if not pages:
            return "No relevant information found in knowledge base."
        
        current_pages = [p for p in pages if p['is_current_year']]
        outdated_pages = [p for p in pages if not p['is_current_year']]
        
        guidance = []
        
        if current_pages:
            guidance.append(f"✅ {len(current_pages)} current school year ({self.current_year}) sources available - PRIORITIZE THESE")
            for page in current_pages[:3]:  # Top 3 current sources
                guidance.append(f"  - {page['url']} (Recency: {page['recency_score']:.2f})")
        
        if outdated_pages:
            guidance.append(f"⚠️  {len(outdated_pages)} outdated sources available - USE WITH CAUTION")
            for page in outdated_pages[:2]:  # Top 2 outdated sources
                guidance.append(f"  - {page['url']} (Year: {page['school_year']}, Recency: {page['recency_score']:.2f})")
        
        return "\n".join(guidance)