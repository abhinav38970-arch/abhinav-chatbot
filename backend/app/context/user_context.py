"""
User Context System

This system manages user-specific context including:
- User roles and permissions
- School and grade level context
- Conversation memory and history
- Personalization preferences

Features:
- Role-based access control
- School-specific context management
- Session conversation memory
- Context persistence and retrieval
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

logger = logging.getLogger("user_context")

@dataclass
class UserProfile:
    """Comprehensive user profile with role and context information"""
    user_id: str
    role: str  # student, parent, staff, admin
    school_id: str
    school_name: str
    school_level: str  # high, middle, elementary, district
    grade_level: Optional[str] = None  # 9, 10, 11, 12, etc.
    student_id: Optional[str] = None  # For parents linking to students
    preferences: Optional[Dict] = None
    created_at: str = datetime.now().isoformat()
    last_updated: str = datetime.now().isoformat()

class UserContextManager:
    """Advanced user context management system"""
    
    def __init__(self):
        # User context storage
        self.user_contexts = {}  # {user_id: UserProfile}
        self.active_sessions = {}  # {session_id: user_id}
        self.conversation_memory = {}  # {session_id: [messages]}
        
        # Role definitions and permissions
        self.role_permissions = {
            'student': {
                'access_level': 1,
                'can_access': ['personal_info', 'grades', 'schedule', 'assignments'],
                'school_scope': 'single'
            },
            'parent': {
                'access_level': 2,
                'can_access': ['student_info', 'grades', 'schedule', 'communications', 'district_policies'],
                'school_scope': 'multiple'  # Can access multiple schools for their children
            },
            'staff': {
                'access_level': 3,
                'can_access': ['student_records', 'school_policies', 'staff_resources', 'district_resources'],
                'school_scope': 'single'  # Typically tied to one school
            },
            'admin': {
                'access_level': 4,
                'can_access': ['all_records', 'district_policies', 'system_settings'],
                'school_scope': 'district'  # District-wide access
            }
        }
        
        # School level mappings
        self.school_levels = {
            'elementary': ['K', '1', '2', '3', '4', '5'],
            'middle': ['6', '7', '8'],
            'high': ['9', '10', '11', '12'],
            'district': []  # No specific grades
        }
        
        logger.info("✅ User context manager initialized")
        
    def create_user_context(self, user_data: Dict) -> Tuple[bool, Optional[str]]:
        """Create a new user context"""
        try:
            # Validate required fields
            required_fields = ['user_id', 'role', 'school_id']
            for field in required_fields:
                if field not in user_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return False, f"Missing required field: {field}"
            
            # Get school information
            school_id = user_data['school_id']
            school_name = user_data.get('school_name', f"School {school_id}")
            school_level = user_data.get('school_level', 'district')
            
            # Validate school level
            if school_level not in self.school_levels:
                logger.error(f"❌ Invalid school level: {school_level}")
                return False, f"Invalid school level: {school_level}"
            
            # Validate role
            role = user_data['role']
            if role not in self.role_permissions:
                logger.error(f"❌ Invalid role: {role}")
                return False, f"Invalid role: {role}"
            
            # Validate grade level if provided
            grade_level = user_data.get('grade_level')
            if grade_level and grade_level not in self.school_levels[school_level]:
                logger.error(f"❌ Invalid grade level {grade_level} for school level {school_level}")
                return False, f"Invalid grade level {grade_level} for school level {school_level}"
            
            # Create user profile
            user_profile = UserProfile(
                user_id=user_data['user_id'],
                role=role,
                school_id=school_id,
                school_name=school_name,
                school_level=school_level,
                grade_level=grade_level,
                student_id=user_data.get('student_id'),
                preferences=user_data.get('preferences', {})
            )
            
            # Store user context
            self.user_contexts[user_data['user_id']] = user_profile
            
            logger.info(f"👤 Created user context: {user_data['user_id']} ({role} at {school_name})")
            
            return True, user_data['user_id']
            
        except Exception as e:
            logger.error(f"❌ Failed to create user context: {str(e)}")
            return False, str(e)
        
    def get_user_context(self, user_id: str) -> Optional[UserProfile]:
        """Get user context by user ID"""
        return self.user_contexts.get(user_id)
        
    def update_user_context(self, user_id: str, updates: Dict) -> Tuple[bool, Optional[str]]:
        """Update user context"""
        if user_id not in self.user_contexts:
            return False, f"User {user_id} not found"
        
        try:
            user_profile = self.user_contexts[user_id]
            
            # Update allowed fields
            allowed_updates = ['grade_level', 'student_id', 'preferences']
            for field, value in updates.items():
                if field in allowed_updates:
                    setattr(user_profile, field, value)
            
            # Update timestamp
            user_profile.last_updated = datetime.now().isoformat()
            
            logger.info(f"🔄 Updated user context: {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"❌ Failed to update user context: {str(e)}")
            return False, str(e)
        
    def delete_user_context(self, user_id: str) -> bool:
        """Delete user context"""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            logger.info(f"🗑️  Deleted user context: {user_id}")
            return True
        return False
        
    def start_user_session(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Start a new user session"""
        if user_id not in self.user_contexts:
            return False, f"User {user_id} not found"
        
        try:
            # Generate session ID
            session_id = self._generate_session_id(user_id)
            
            # Store session
            self.active_sessions[session_id] = user_id
            self.conversation_memory[session_id] = []
            
            logger.info(f"🔑 Started session: {session_id} for user {user_id}")
            return True, session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to start session: {str(e)}")
            return False, str(e)
        
    def end_user_session(self, session_id: str) -> bool:
        """End a user session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            del self.conversation_memory[session_id]
            logger.info(f"🔑 Ended session: {session_id}")
            return True
        return False
        
    def get_session_user(self, session_id: str) -> Optional[str]:
        """Get user ID for a session"""
        return self.active_sessions.get(session_id)
        
    def add_conversation_memory(self, session_id: str, message: Dict) -> bool:
        """Add message to conversation memory"""
        if session_id in self.conversation_memory:
            self.conversation_memory[session_id].append({
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'message_hash': self._generate_message_hash(message)
            })
            return True
        return False
        
    def get_conversation_memory(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation memory for a session"""
        if session_id in self.conversation_memory:
            return list(self.conversation_memory[session_id])[-limit:]
        return []
        
    def clear_conversation_memory(self, session_id: str) -> bool:
        """Clear conversation memory for a session"""
        if session_id in self.conversation_memory:
            self.conversation_memory[session_id] = []
            return True
        return False
        
    def get_user_context_with_session(self, session_id: str) -> Optional[Tuple[UserProfile, List[Dict]]]:
        """Get user context and conversation memory by session ID"""
        user_id = self.get_session_user(session_id)
        if user_id:
            user_profile = self.get_user_context(user_id)
            conversation = self.get_conversation_memory(session_id)
            return user_profile, conversation
        return None
        
    def check_permission(self, session_id: str, resource_type: str) -> Tuple[bool, Optional[str]]:
        """Check if user has permission to access a resource"""
        user_id = self.get_session_user(session_id)
        if not user_id:
            return False, "Invalid session"
        
        user_profile = self.get_user_context(user_id)
        if not user_profile:
            return False, "User not found"
        
        role_permissions = self.role_permissions.get(user_profile.role, {})
        allowed_resources = role_permissions.get('can_access', [])
        
        if resource_type in allowed_resources:
            return True, None
        else:
            return False, f"Role {user_profile.role} cannot access {resource_type}"
        
    def get_school_context(self, session_id: str) -> Optional[Dict]:
        """Get school context for a session"""
        user_profile, _ = self.get_user_context_with_session(session_id)
        if user_profile:
            return {
                'school_id': user_profile.school_id,
                'school_name': user_profile.school_name,
                'school_level': user_profile.school_level,
                'grade_level': user_profile.grade_level
            }
        return None
        
    def get_personalization_context(self, session_id: str) -> Dict:
        """Get personalization context for a session"""
        user_profile, conversation = self.get_user_context_with_session(session_id)
        
        context = {
            'role': user_profile.role if user_profile else 'anonymous',
            'school_level': user_profile.school_level if user_profile else 'district',
            'grade_level': user_profile.grade_level if user_profile else None,
            'conversation_history': len(conversation) if conversation else 0,
            'preferences': user_profile.preferences if user_profile else {}
        }
        
        return context
        
    def _generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{user_id}_{timestamp}".encode()).hexdigest()
        
    def _generate_message_hash(self, message: Dict) -> str:
        """Generate hash for message deduplication"""
        message_str = json.dumps(message, sort_keys=True)
        return hashlib.md5(message_str.encode()).hexdigest()
        
    def get_system_stats(self) -> Dict:
        """Get user context system statistics"""
        return {
            'total_users': len(self.user_contexts),
            'active_sessions': len(self.active_sessions),
            'total_conversations': len(self.conversation_memory),
            'roles_distribution': self._get_roles_distribution(),
            'schools_distribution': self._get_schools_distribution()
        }
        
    def _get_roles_distribution(self) -> Dict:
        """Get distribution of user roles"""
        distribution = {}
        for user_profile in self.user_contexts.values():
            role = user_profile.role
            distribution[role] = distribution.get(role, 0) + 1
        return distribution
        
    def _get_schools_distribution(self) -> Dict:
        """Get distribution of schools"""
        distribution = {}
        for user_profile in self.user_contexts.values():
            school_id = user_profile.school_id
            distribution[school_id] = distribution.get(school_id, 0) + 1
        return distribution
        
    def reset_system(self) -> None:
        """Reset user context system (for testing)"""
        self.user_contexts = {}
        self.active_sessions = {}
        self.conversation_memory = {}
        logger.info("🔄 User context system reset")

# Example usage
if __name__ == "__main__":
    # Initialize user context manager
    context_manager = UserContextManager()
    
    # Create user context
    user_data = {
        'user_id': 'student_12345',
        'role': 'student',
        'school_id': 'washington',
        'school_name': 'Washington High School',
        'school_level': 'high',
        'grade_level': '11',
        'preferences': {'theme': 'dark', 'notifications': True}
    }
    
    success, user_id = context_manager.create_user_context(user_data)
    print(f"User creation: {'success' if success else 'failed'}")
    
    # Start session
    success, session_id = context_manager.start_user_session(user_id)
    print(f"Session creation: {'success' if success else 'failed'}")
    
    # Get context
    user_profile, conversation = context_manager.get_user_context_with_session(session_id)
    print(f"User profile: {user_profile.role} at {user_profile.school_name}")
    
    # Check permission
    can_access, reason = context_manager.check_permission(session_id, 'grades')
    print(f"Can access grades: {can_access} ({reason if reason else 'allowed'})")
    
    # Get personalization context
    personalization = context_manager.get_personalization_context(session_id)
    print(f"Personalization context: {personalization}")
    
    # End session
    context_manager.end_user_session(session_id)
    print("Session ended")
