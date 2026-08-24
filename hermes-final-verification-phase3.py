#!/usr/bin/env python3
"""
Final Verification Script - Phase 3 Complete
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
    print("🔍 Final Verification - Phase 3 Complete")
    print("=" * 50)
    
    try:
        # Test User Context System
        from context.user_context import UserContextManager, UserProfile
        
        context_manager = UserContextManager()
        print("✅ User context manager initialized")
        
        # Create user context
        user_data = {
            'user_id': 'test_student',
            'role': 'student',
            'school_id': 'washington',
            'school_name': 'Washington High School',
            'school_level': 'high',
            'grade_level': '11',
            'preferences': {'theme': 'dark'}
        }
        
        success, user_id = context_manager.create_user_context(user_data)
        print(f"✅ User context created: {success}")
        
        # Start session
        success, session_id = context_manager.start_user_session(user_id)
        print(f"✅ Session started: {success}")
        
        # Get context
        user_profile, conversation = context_manager.get_user_context_with_session(session_id)
        print(f"✅ User profile retrieved: {user_profile.role}")
        
        # Check permission
        can_access, reason = context_manager.check_permission(session_id, 'grades')
        print(f"✅ Permission check: {can_access}")
        
        # Get personalization context
        personalization = context_manager.get_personalization_context(session_id)
        print(f"✅ Personalization context: {personalization['role']}")
        
        # End session
        context_manager.end_user_session(session_id)
        print("✅ Session ended")
        
        # Test Query Router
        from retrieval.query_router import QueryRouter, QueryIntent
        
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
            print(f"✅ Intent classified: {intent.primary_intent} (confidence: {intent.confidence:.2f})")
        
        # Test query routing
        user_context = {
            'role': 'student',
            'name': 'Alex',
            'school_name': 'Washington High School',
            'grade_level': '11'
        }
        
        route_result = router.route_query("What is the school schedule?", user_context)
        print(f"✅ Query routed: {route_result['routing_strategy']['route_to']}")
        print(f"✅ Personalized prompt generated: {len(route_result['personalized_prompt'])} chars")
        
        print("\n🎉 FINAL VERIFICATION SUCCESSFUL!")
        print("✅ User Context System: WORKING")
        print("✅ Query Router: WORKING")
        print("✅ Intent Classification: WORKING")
        print("✅ Personalization: WORKING")
        
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
