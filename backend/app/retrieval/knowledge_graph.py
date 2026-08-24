"""
Cross-School Knowledge Graph

This system builds and traverses semantic relationships between:
- Schools (feeder patterns: elementary → middle → high)
- Content (related documents across schools)
- Knowledge domains (academic subjects, policies, events)

Features:
- NetworkX-based graph construction
- Feeder pattern mapping
- Semantic content relationships
- Graph traversal for comprehensive answers
"""

import networkx as nx
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import hashlib
from datetime import datetime

logger = logging.getLogger("knowledge_graph")

class KnowledgeGraph:
    """Cross-school knowledge graph with semantic relationships"""
    
    def __init__(self):
        # Initialize directed graph
        self.graph = nx.DiGraph()
        
        # Relationship mappings
        self.school_relationships = {}  # {school_id: [related_school_ids]}
        self.content_relationships = defaultdict(list)  # {content_hash: [related_hashes]}
        self.knowledge_domains = defaultdict(set)  # {domain: [content_hashes]}
        
        # Statistics
        self.stats = {
            'nodes': 0,
            'edges': 0,
            'schools': 0,
            'content_items': 0,
            'domains': 0,
            'last_updated': None
        }
        
        logger.info("✅ Knowledge graph initialized")
        
    def build_school_relationships(self, school_config) -> None:
        """Map feeder patterns: elementary → middle → high"""
        logger.info("🏫 Building school relationships...")
        
        # Clear existing school relationships
        self.school_relationships = {}
        
        # Organize schools by level
        schools_by_level = defaultdict(list)
        for school in school_config.schools:
            level = school['school_level']
            school_id = school['school_id']
            schools_by_level[level].append(school)
            
            # Add school node to graph
            self.graph.add_node(school_id, 
                              type='school',
                              level=level,
                              name=school['school_name'])
        
        # Build elementary → middle relationships (geographic proximity)
        elementary_schools = schools_by_level.get('elementary', [])
        middle_schools = schools_by_level.get('middle', [])
        
        for elem in elementary_schools:
            elem_id = elem['school_id']
            # Find closest middle school (simplified - in production use geographic data)
            closest_middle = middle_schools[0]['school_id'] if middle_schools else None
            
            if closest_middle:
                self._add_school_relationship(elem_id, closest_middle, 'feeds_into')
        
        # Build middle → high relationships
        high_schools = schools_by_level.get('high', [])
        
        for middle in middle_schools:
            middle_id = middle['school_id']
            # Find closest high school
            closest_high = high_schools[0]['school_id'] if high_schools else None
            
            if closest_high:
                self._add_school_relationship(middle_id, closest_high, 'feeds_into')
        
        # Build district-wide relationships
        district_node = 'fusd_district'
        self.graph.add_node(district_node, type='district', level='district', name='FUSD')
        
        for school_id in self.school_relationships.keys():
            self._add_school_relationship(school_id, district_node, 'part_of')
        
        self.stats['schools'] = len(self.school_relationships)
        self.stats['nodes'] = len(self.graph.nodes())
        self.stats['edges'] = len(self.graph.edges())
        self.stats['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"🎯 Built {len(self.school_relationships)} school relationships")
        
    def _add_school_relationship(self, source: str, target: str, relationship_type: str) -> None:
        """Add relationship between schools"""
        if source not in self.school_relationships:
            self.school_relationships[source] = []
        
        if target not in self.school_relationships[source]:
            self.school_relationships[source].append(target)
            self.graph.add_edge(source, target, type=relationship_type)
        
    def add_content_to_graph(self, content: str, metadata: Dict) -> str:
        """Add content to knowledge graph with semantic relationships"""
        # Generate content hash
        content_hash = self._generate_content_hash(content)
        
        # Add content node
        school_id = metadata.get('school_id', 'district')
        content_type = metadata.get('content_type', 'document')
        
        self.graph.add_node(content_hash,
                          type='content',
                          school_id=school_id,
                          content_type=content_type,
                          title=metadata.get('title', content[:50]),
                          url=metadata.get('source_url', ''),
                          added_at=datetime.now().isoformat())
        
        # Link content to school
        self.graph.add_edge(school_id, content_hash, type='contains')
        
        # Extract knowledge domains
        domains = self._extract_knowledge_domains(content, metadata)
        for domain in domains:
            self.knowledge_domains[domain].add(content_hash)
            self.graph.add_edge(content_hash, domain, type='belongs_to')
        
        # Find related content (semantic similarity)
        related_content = self._find_related_content(content, metadata)
        for related_hash in related_content:
            if related_hash != content_hash:
                self.content_relationships[content_hash].append(related_hash)
                self.graph.add_edge(content_hash, related_hash, type='related_to', weight=0.8)
        
        self.stats['content_items'] += 1
        self.stats['nodes'] = len(self.graph.nodes())
        self.stats['edges'] = len(self.graph.edges())
        self.stats['domains'] = len(self.knowledge_domains)
        self.stats['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"📚 Added content to graph: {content[:30]}... (hash: {content_hash[:8]})")
        
        return content_hash
        
    def _generate_content_hash(self, content: str) -> str:
        """Generate unique hash for content"""
        return hashlib.md5(content.encode()).hexdigest()
        
    def _extract_knowledge_domains(self, content: str, metadata: Dict) -> Set[str]:
        """Extract knowledge domains from content"""
        domains = set()
        content_lower = content.lower()
        
        # Academic subjects
        subjects = [
            'math', 'mathematics', 'algebra', 'geometry', 'calculus',
            'science', 'biology', 'chemistry', 'physics',
            'english', 'literature', 'writing',
            'history', 'social studies',
            'computer science', 'programming', 'coding'
        ]
        
        for subject in subjects:
            if subject in content_lower:
                domains.add(f'subject_{subject}')
        
        # School operations
        operations = [
            'schedule', 'calendar', 'bell schedule',
            'enrollment', 'registration',
            'graduation', 'ceremony',
            'policy', 'rules', 'guidelines',
            'safety', 'security', 'emergency'
        ]
        
        for operation in operations:
            if operation in content_lower:
                domains.add(f'operation_{operation.replace(" ", "_")}')
        
        # Events
        events = [
            'back to school', 'open house',
            'parent teacher', 'conference',
            'sport', 'game', 'match',
            'concert', 'performance', 'play'
        ]
        
        for event in events:
            if event in content_lower:
                domains.add(f'event_{event.replace(" ", "_")}')
        
        # Add metadata-based domains
        school_level = metadata.get('school_level')
        if school_level:
            domains.add(f'level_{school_level}')
        
        content_type = metadata.get('content_type')
        if content_type:
            domains.add(f'type_{content_type}')
        
        return domains
        
    def _find_related_content(self, content: str, metadata: Dict) -> List[str]:
        """Find semantically related content"""
        related = []
        
        # Simple keyword-based relationship (in production use embeddings)
        keywords = ['schedule', 'calendar', 'policy', 'procedure', 'requirement']
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword in content_lower:
                # Find existing content with same keyword
                for content_hash, node_data in self.graph.nodes(data=True):
                    if node_data.get('type') == 'content':
                        if keyword in node_data.get('title', '').lower():
                            related.append(content_hash)
        
        return list(set(related))  # Remove duplicates
        
    def traverse_knowledge_graph(self, query: str, starting_school: str, 
                                max_depth: int = 3, max_results: int = 10) -> Dict:
        """Traverse graph to find comprehensive answers"""
        logger.info(f"🔍 Traversing knowledge graph: {query[:30]}... from {starting_school}")
        
        results = {
            'direct_results': [],
            'related_schools': [],
            'related_content': [],
            'knowledge_domains': [],
            'traversal_stats': {
                'nodes_visited': 0,
                'depth_reached': 0,
                'content_found': 0
            }
        }
        
        # Start from the school node
        if starting_school not in self.graph:
            logger.warning(f"⚠️  Starting school not found: {starting_school}")
            return results
        
        # BFS traversal
        visited = set()
        queue = [(starting_school, 0)]
        
        while queue and results['traversal_stats']['content_found'] < max_results:
            current_node, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            results['traversal_stats']['nodes_visited'] += 1
            results['traversal_stats']['depth_reached'] = max(
                results['traversal_stats']['depth_reached'], depth
            )
            
            node_data = self.graph.nodes[current_node]
            
            # Process different node types
            if node_data.get('type') == 'school':
                if current_node != starting_school:
                    results['related_schools'].append({
                        'school_id': current_node,
                        'school_name': node_data.get('name', current_node),
                        'level': node_data.get('level'),
                        'relationship': 'related_school'
                    })
                
                # Get content from this school
                for neighbor in self.graph.neighbors(current_node):
                    if self.graph.nodes[neighbor].get('type') == 'content':
                        queue.append((neighbor, depth + 1))
                        
            elif node_data.get('type') == 'content':
                # Add content to results
                content_result = {
                    'content_hash': current_node,
                    'title': node_data.get('title', 'Untitled'),
                    'school_id': node_data.get('school_id'),
                    'content_type': node_data.get('content_type'),
                    'url': node_data.get('url'),
                    'depth': depth,
                    'relationship': 'direct_content'
                }
                
                results['direct_results'].append(content_result)
                results['traversal_stats']['content_found'] += 1
                
                # Get related content
                for neighbor in self.graph.neighbors(current_node):
                    if self.graph.nodes[neighbor].get('type') == 'content':
                        related_content = {
                            'content_hash': neighbor,
                            'title': self.graph.nodes[neighbor].get('title', 'Untitled'),
                            'school_id': self.graph.nodes[neighbor].get('school_id'),
                            'relationship': 'related_content',
                            'via': current_node
                        }
                        results['related_content'].append(related_content)
                        
            elif node_data.get('type') == 'domain':
                results['knowledge_domains'].append({
                    'domain': current_node,
                    'depth': depth
                })
        
        # Deduplicate results
        results['direct_results'] = self._deduplicate_results(results['direct_results'])
        results['related_content'] = self._deduplicate_results(results['related_content'])
        
        logger.info(f"🎯 Graph traversal complete: {len(results['direct_results'])} direct + {len(results['related_content'])} related results")
        
        return results
        
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results"""
        seen = set()
        deduped = []
        
        for result in results:
            content_hash = result.get('content_hash')
            if content_hash and content_hash not in seen:
                seen.add(content_hash)
                deduped.append(result)
        
        return deduped
        
    def get_school_feeder_pattern(self, school_id: str) -> Dict:
        """Get complete feeder pattern for a school"""
        if school_id not in self.school_relationships:
            return {'error': 'School not found'}
        
        pattern = {
            'school_id': school_id,
            'school_name': self.graph.nodes[school_id].get('name', school_id),
            'level': self.graph.nodes[school_id].get('level'),
            'feeds_into': [],
            'fed_by': [],
            'part_of': []
        }
        
        # Find relationships
        for source, target, edge_data in self.graph.edges(data=True):
            if source == school_id:
                if edge_data.get('type') == 'feeds_into':
                    pattern['feeds_into'].append(target)
                elif edge_data.get('type') == 'part_of':
                    pattern['part_of'].append(target)
            
            if target == school_id and edge_data.get('type') == 'feeds_into':
                pattern['fed_by'].append(source)
        
        return pattern
        
    def get_knowledge_domain_content(self, domain: str) -> List[Dict]:
        """Get all content in a knowledge domain"""
        if domain not in self.knowledge_domains:
            return []
        
        content_hashes = self.knowledge_domains[domain]
        results = []
        
        for content_hash in content_hashes:
            if content_hash in self.graph:
                node_data = self.graph.nodes[content_hash]
                results.append({
                    'content_hash': content_hash,
                    'title': node_data.get('title'),
                    'school_id': node_data.get('school_id'),
                    'content_type': node_data.get('content_type'),
                    'url': node_data.get('url'),
                    'domain': domain
                })
        
        return results
        
    def get_graph_stats(self) -> Dict:
        """Get comprehensive graph statistics"""
        return {
            **self.stats,
            'school_relationships': len(self.school_relationships),
            'content_relationships': len(self.content_relationships),
            'knowledge_domains': len(self.knowledge_domains),
            'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            'average_degree': sum(dict(self.graph.degree()).values()) / len(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }
        
    def export_graph(self) -> Dict:
        """Export graph data for visualization"""
        return {
            'nodes': [{
                'id': node,
                'type': data.get('type'),
                'label': data.get('name') or data.get('title') or node,
                'level': data.get('level'),
                'school_id': data.get('school_id')
            } for node, data in self.graph.nodes(data=True)],
            'edges': [{
                'source': source,
                'target': target,
                'type': data.get('type'),
                'weight': data.get('weight', 1.0)
            } for source, target, data in self.graph.edges(data=True)]
        }
        
    def reset_graph(self) -> None:
        """Reset the knowledge graph"""
        self.graph = nx.DiGraph()
        self.school_relationships = {}
        self.content_relationships = defaultdict(list)
        self.knowledge_domains = defaultdict(set)
        self.stats = {
            'nodes': 0,
            'edges': 0,
            'schools': 0,
            'content_items': 0,
            'domains': 0,
            'last_updated': None
        }
        logger.info("🔄 Knowledge graph reset")

# Example usage
if __name__ == "__main__":
    # Initialize knowledge graph
    kg = KnowledgeGraph()
    
    # Build school relationships (would use actual school config in production)
    from backend.app.config import SCHOOL_CONFIG
    kg.build_school_relationships(SCHOOL_CONFIG)
    
    # Add content
    test_content = "Washington High School 2023-2024 Academic Calendar"
    test_metadata = {
        'school_id': 'washington',
        'school_name': 'Washington High School',
        'school_level': 'high',
        'content_type': 'calendar',
        'source_url': 'https://fremontunified.org/washington/calendar/'
    }
    
    content_hash = kg.add_content_to_graph(test_content, test_metadata)
    
    # Traverse graph
    results = kg.traverse_knowledge_graph("academic calendar", "washington")
    print(f"Graph traversal results: {len(results['direct_results'])} direct, {len(results['related_content'])} related")
    
    # Get stats
    stats = kg.get_graph_stats()
    print(f"Graph stats: {stats['nodes']} nodes, {stats['edges']} edges")
