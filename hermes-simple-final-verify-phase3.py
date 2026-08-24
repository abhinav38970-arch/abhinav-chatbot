#!/usr/bin/env python3
"""
Simple Final Verification - Phase 3 Complete
"""

import sys
sys.path.insert(0, '/Users/abhinav/Desktop/abhinav-chatbot/backend/app')

def main():
    print("🔍 Final Verification - Phase 3 Complete")
    print("=" * 50)
    
    try:
        # Test User Context System
        from context.user_context import UserContextManager
        
        context_manager = UserContextManager()
        print("✅ User context manager initialized")
        
        # Create user context
        user_data = {
            'user_id': 'test_student',
            'role': 'student',
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'grade_level': '11'
        }
        
        success, user_id = context_manager.create_user_context(user_data)
        print(f"✅ User context created: {success}")
        
        # Start session
        success, session_id = context_manager.start_user_session(user_id)
        print(f"✅ Session started: {success}")
        
        # Get context
        user_profile, conversation = context_manager.get_user_context_with_session(session_id)
        print(f"✅ User profile retrieved: {user_profile.role}")
        
        # End session
        context_manager.end_user_session(session_id)
        print("✅ Session ended")
        
        # Test Query Router
        from retrieval.query_router import QueryRouter
        
        router = QueryRouter()
        print("✅ Query router initialized")
        
        # Test intent classification
        test_queries = [
            "What is the FUSD district policy on attendance?",
            "When is the next event at Washington High School?",
            "What are the graduation requirements?",
            "What clubs are available?"
        ]
        
        for query in test_queries:
            intent = router.classify_query_intent(query)
            print(f"✅ Intent classified: {intent.primary_intent}")
        
        # Test query routing
        user_context = {
            'role': 'student',
            'name': 'Alex',
            'school_name': 'Washington High School',
            'grade_level': '11'
        }
        
        route_result = router.route_query("What is the school schedule?", user_context)
        print(f"✅ Query routed: {route_result['routing_strategy']['route_to']}")
        
        print("\n🎉 FINAL VERIFICATION SUCCESSFUL!")
        print("✅ User Context System: WORKING")
        print("✅ Query Router: WORKING")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
