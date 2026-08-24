"""
Query Router

This system routes queries based on:
- Intent classification
- User context
- Query complexity
- Domain specificity

Features:
- Intent-based routing
- Dynamic prompt personalization
- Context-aware query handling
- Multi-stage query processing
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import json
from datetime import datetime

logger = logging.getLogger("query_router")

@dataclass
class QueryIntent:
    """Structured query intent classification"""
    primary_intent: str
    secondary_intents: List[str]
    confidence: float
    context_required: bool
    personalization_needed: bool

class QueryRouter:
    """Advanced query routing system"""
    
    def __init__(self):
        # Intent classification patterns
        self.intent_patterns = {
            'district_policy': {
                'patterns': [
                    r'\bdistrict\s*(policy|policies|rule|rules|guideline|guidelines)\b',
                    r'\bfusd\s*(policy|policies|rule|rules)\b',
                    r'\bboard\s*policy\b',
                    r'\bdistrict-wide\s*(requirement|requirements)\b'
                ],
                'context_required': False,
                'personalization_needed': False
            },
            'school_specific': {
                'patterns': [
                    r'\bschool\s*(schedule|calendar|event|events|activity|activities)\b',
                    r'\b(specific\s+)?school\s*(policy|policies|rule|rules)\b',
                    r'\b(washington|irvington|kennedy|mission san jose)\s*(high school|high)\b',
                    r'\bmy\s*school\b'
                ],
                'context_required': True,
                'personalization_needed': True
            },
            'academic': {
                'patterns': [
                    r'\b(grade|grades|transcript|report card|GPA)\b',
                    r'\b(assignment|homework|test|quiz|exam)\b',
                    r'\b(curriculum|course|class|subject)\b',
                    r'\b(graduation|requirement|requirements|credit)\b',
                    r'\b(AP|Advanced Placement|honors|IB)\b'
                ],
                'context_required': True,
                'personalization_needed': True
            },
            'extracurricular': {
                'patterns': [
                    r'\b(club|clubs|activity|activities|sport|sports|team|teams)\b',
                    r'\b(after\s*school|afterschool)\b',
                    r'\b(student\s*council|student\s*government)\b',
                    r'\b(art|music|drama|theater|band|choir)\b',
                    r'\b(competition|tournament|meet|match)\b'
                ],
                'context_required': True,
                'personalization_needed': True
            },
            'general_information': {
                'patterns': [
                    r'\b(contact|phone|address|location|hours|office)\b',
                    r'\b(principal|administrator|staff|teacher)\b',
                    r'\b(about|information|details|description)\b',
                    r'\b(history|background|mission|vision)\b'
                ],
                'context_required': False,
                'personalization_needed': False
            },
            'technical_support': {
                'patterns': [
                    r'\b(technical|tech|support|help|issue|problem|error)\b',
                    r'\b(password|login|account|access|permission)\b',
                    r'\b(website|portal|system|software|app)\b',
                    r'\b(computer|device|technology|internet)\b'
                ],
                'context_required': False,
                'personalization_needed': False
            }
        }
        
        # Intent confidence thresholds
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
        
        # Personalization templates
        self.personalization_templates = {
            'student': {
                'greeting': "Hello {name}! As a {grade_level} grade student at {school_name}, here's what I found for you:",
                'context': "Based on your student profile and academic level, I've personalized this information for you."
            },
            'parent': {
                'greeting': "Hello {name}! As a parent of a {grade_level} grade student at {school_name}, here's the information you requested:",
                'context': "This information is tailored for parents and includes relevant family resources."
            },
            'staff': {
                'greeting': "Hello {name}! As staff at {school_name}, here's the professional information you requested:",
                'context': "This includes staff-specific resources and administrative details."
            },
            'admin': {
                'greeting': "Hello {name}! As FUSD administrator, here's the comprehensive information:",
                'context': "This includes district-wide administrative resources and policy details."
            }
        }
        
        logger.info("✅ Query router initialized")
        
    def classify_query_intent(self, query: str) -> QueryIntent:
        """Classify query intent using pattern matching"""
        logger.info(f"🔍 Classifying query intent: {query[:50]}...")
        
        # Initialize intent classification
        intent_scores = {}
        
        # Check each intent pattern
        for intent_name, intent_config in self.intent_patterns.items():
            score = 0.0
            
            for pattern in intent_config['patterns']:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1.0 / len(intent_config['patterns'])
            
            if score > 0:
                intent_scores[intent_name] = score
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])
            primary_intent_name = primary_intent[0]
            primary_intent_score = primary_intent[1]
            
            # Calculate confidence
            confidence = min(primary_intent_score * 1.2, 1.0)  # Boost slightly but cap at 1.0
            
            # Get secondary intents (scores > 0.3)
            secondary_intents = [
                intent for intent, score in intent_scores.items() 
                if intent != primary_intent_name and score > 0.3
            ]
            
            # Get context requirements
            context_required = self.intent_patterns[primary_intent_name]['context_required']
            personalization_needed = self.intent_patterns[primary_intent_name]['personalization_needed']
            
            logger.info(f"🎯 Intent classified: {primary_intent_name} (confidence: {confidence:.3f})")
            
            return QueryIntent(
                primary_intent=primary_intent_name,
                secondary_intents=secondary_intents,
                confidence=confidence,
                context_required=context_required,
                personalization_needed=personalization_needed
            )
        else:
            logger.info("🎯 Intent classified: general (no specific pattern match)")
            return QueryIntent(
                primary_intent='general',
                secondary_intents=[],
                confidence=0.5,
                context_required=False,
                personalization_needed=False
            )
        
    def route_query(self, query: str, user_context: Optional[Dict] = None) -> Dict:
        """Route query based on intent and user context"""
        logger.info(f"🚦 Routing query: {query[:50]}...")
        
        # Classify intent
        intent = self.classify_query_intent(query)
        
        # Determine routing strategy
        routing_strategy = self._determine_routing_strategy(intent, user_context)
        
        # Generate personalized prompt
        personalized_prompt = self.generate_personalized_prompt(query, intent, user_context)
        
        # Create routing result
        result = {
            'original_query': query,
            'intent': {
                'primary': intent.primary_intent,
                'secondary': intent.secondary_intents,
                'confidence': intent.confidence,
                'context_required': intent.context_required,
                'personalization_needed': intent.personalization_needed
            },
            'routing_strategy': routing_strategy,
            'personalized_prompt': personalized_prompt,
            'context_used': user_context is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📍 Query routed: {routing_strategy['route_to']}")
        
        return result
        
    def _determine_routing_strategy(self, intent: QueryIntent, 
                                   user_context: Optional[Dict] = None) -> Dict:
        """Determine optimal routing strategy"""
        strategy = {
            'route_to': 'general',
            'priority': 'normal',
            'context_required': intent.context_required,
            'personalization_level': 'none'
        }
        
        # Route based on intent
        if intent.primary_intent == 'district_policy':
            strategy['route_to'] = 'district_policy_engine'
            strategy['priority'] = 'high'
        
        elif intent.primary_intent == 'school_specific':
            strategy['route_to'] = 'school_specific_retriever'
            strategy['priority'] = 'high'
            
            if user_context and user_context.get('school_id'):
                strategy['context_required'] = True
                strategy['personalization_level'] = 'high'
        
        elif intent.primary_intent == 'academic':
            strategy['route_to'] = 'academic_retriever'
            strategy['priority'] = 'high'
            
            if user_context and user_context.get('grade_level'):
                strategy['context_required'] = True
                strategy['personalization_level'] = 'high'
        
        elif intent.primary_intent == 'extracurricular':
            strategy['route_to'] = 'extracurricular_retriever'
            strategy['priority'] = 'medium'
            
            if user_context and user_context.get('school_id'):
                strategy['context_required'] = True
                strategy['personalization_level'] = 'medium'
        
        elif intent.primary_intent == 'general_information':
            strategy['route_to'] = 'general_info_retriever'
            strategy['priority'] = 'medium'
        
        elif intent.primary_intent == 'technical_support':
            strategy['route_to'] = 'technical_support'
            strategy['priority'] = 'critical'
        
        else:  # general intent
            strategy['route_to'] = 'general_retriever'
            strategy['priority'] = 'low'
        
        return strategy
        
    def generate_personalized_prompt(self, query: str, intent: QueryIntent, 
                                    user_context: Optional[Dict] = None) -> str:
        """Generate personalized prompt based on user context"""
        base_prompt = f"Query: {query}\n\n"
        
        if not user_context or not intent.personalization_needed:
            return base_prompt + "Please provide general information about this topic."
        
        # Extract user context
        role = user_context.get('role', 'student')
        school_name = user_context.get('school_name', 'FUSD')
        grade_level = user_context.get('grade_level', 'student')
        name = user_context.get('name', 'User')
        
        # Get personalization template
        template = self.personalization_templates.get(role, self.personalization_templates['student'])
        
        # Generate personalized greeting
        greeting = template['greeting'].format(
            name=name,
            grade_level=grade_level,
            school_name=school_name
        )
        
        # Add context based on intent
        context = template['context']
        
        # Add intent-specific instructions
        intent_instructions = self._get_intent_specific_instructions(intent.primary_intent, user_context)
        
        # Combine all elements
        personalized_prompt = f"""{greeting}

{context}

{intent_instructions}

Original Query: {query}

Please provide detailed, accurate, and helpful information tailored to this user's context."""
        
        return personalized_prompt
        
    def _get_intent_specific_instructions(self, intent: str, user_context: Dict) -> str:
        """Get intent-specific instructions for prompt generation"""
        instructions = ""
        
        if intent == 'district_policy':
            instructions = "Focus on official FUSD district policies. Include relevant policy numbers, dates, and contact information for the district office."
        
        elif intent == 'school_specific':
            school_name = user_context.get('school_name', 'the school')
            instructions = f"Provide information specific to {school_name}. Include school-specific policies, procedures, and contact information. Mention the school name prominently in the response."
        
        elif intent == 'academic':
            grade_level = user_context.get('grade_level', 'this grade level')
            instructions = f"Tailor academic information for {grade_level} grade students. Include grade-appropriate resources, curriculum details, and academic support information."
        
        elif intent == 'extracurricular':
            school_name = user_context.get('school_name', 'the school')
            instructions = f"Highlight extracurricular activities available at {school_name}. Include club meeting times, coach/advisor contacts, and participation requirements."
        
        elif intent == 'general_information':
            instructions = "Provide general information about FUSD. Include contact information, office hours, and links to official resources."
        
        elif intent == 'technical_support':
            instructions = "Offer technical support guidance. Include troubleshooting steps, contact information for the IT help desk, and links to support resources."
        
        else:
            instructions = "Provide helpful and accurate information. Tailor the response to the user's role and context when possible."
        
        return instructions
        
    def get_query_analytics(self) -> Dict:
        """Get analytics about query routing (would track in production)"""
        return {
            'intent_distribution': {
                'district_policy': 0.15,
                'school_specific': 0.30,
                'academic': 0.25,
                'extracurricular': 0.10,
                'general_information': 0.15,
                'technical_support': 0.05
            },
            'average_confidence': 0.82,
            'personalization_rate': 0.65
        }
        
    def reset_router(self) -> None:
        """Reset query router (for testing)"""
        logger.info("🔄 Query router reset")

# Example usage
if __name__ == "__main__":
    # Initialize query router
    router = QueryRouter()
    
    # Example queries
    queries = [
        "What is the FUSD district policy on student attendance?",
        "When is the next school event at Washington High School?",
        "What are the graduation requirements for 11th grade students?",
        "What clubs are available for students interested in robotics?",
        "What is the phone number for the district office?",
        "I'm having trouble logging into the student portal"
    ]
    
    # Example user context
    user_context = {
        'role': 'student',
        'name': 'Alex',
        'school_name': 'Washington High School',
        'grade_level': '11'
    }
    
    # Route each query
    for query in queries:
        result = router.route_query(query, user_context)
        print(f"\nQuery: {query[:50]}...")
        print(f"Intent: {result['intent']['primary']} (confidence: {result['intent']['confidence']:.2f})")
        print(f"Route to: {result['routing_strategy']['route_to']}")
        print(f"Personalized: {result['personalized_prompt'][:100]}...")
