"""
Husky AI - FUSD Chat Interface

Main Streamlit application for the FUSD chatbot with:
- School selection
- Role selection (Student/Parent/Staff)
- Chat history
- Confidence-weighted citations
- Responsive design
"""

import streamlit as st
import os
import sys
import time
from datetime import datetime

# Add repo root to path so `backend.app.*` imports resolve (works locally AND on cloud)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set page configuration
st.set_page_config(
    page_title="Husky AI - FUSD Chat",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for FUSD theme
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #0066cc;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background-color: #f1f1f1;
        text-align: left;
    }
    .citation {
        font-size: 0.8em;
        color: #666;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'school_selected' not in st.session_state:
    st.session_state.school_selected = None
if 'role_selected' not in st.session_state:
    st.session_state.role_selected = None
if 'user_context' not in st.session_state:
    st.session_state.user_context = None

# Title and description
st.title("🐺 Husky AI - FUSD Chat")
st.markdown("""
    **Welcome to the Fremont Unified School District AI Assistant**
    
    Ask questions about FUSD policies, school information, academic requirements, and more.
    Select your school and role to get personalized answers!
""")

# Sidebar for school and role selection
with st.sidebar:
    st.header("🎓 Your Profile")

    # School selection — all schools from config, grouped by level
    from backend.app.config import SCHOOL_CONFIG
    _schools_by_level = {}
    for _s in SCHOOL_CONFIG.schools:
        _schools_by_level.setdefault(_s["school_level"], []).append(
            (_s["school_name"], _s["school_id"])
        )
    school_options = []
    for _level in ["high", "middle", "elementary", "preschool", "alternative", "adult"]:
        for _name, _sid in sorted(_schools_by_level.get(_level, [])):
            label = f"{_name} ({_level})" if _level != "high" else _name
            school_options.append((label, _sid))

    selected_school_label = st.selectbox(
        "Select Your School",
        [label for label, _ in school_options],
        index=None,
        placeholder="Choose your school..."
    )
    selected_school = selected_school_label  # keep downstream logic simple
    
    if selected_school:
        st.session_state.school_selected = selected_school
        
        # Role selection
        roles = ["Student", "Parent", "Staff"]
        selected_role = st.selectbox(
            "Select Your Role",
            roles,
            index=None,
            placeholder="Choose your role..."
        )
        
        if selected_role:
            st.session_state.role_selected = selected_role
            
            # Initialize user context
            if st.button("🔄 Update Profile"):
                from context.user_context import UserContextManager

                context_manager = UserContextManager()

                # Resolve school_id from the picker (config-driven)
                school_id = dict(school_options).get(selected_school_label, "washington")
                grade_level = "11" if selected_role == "Student" else None
                
                user_data = {
                    'user_id': f"user_{datetime.now().timestamp()}",
                    'role': selected_role.lower(),
                    'school_id': school_id,
                    'school_name': selected_school,
                    'school_level': 'high',
                    'grade_level': grade_level
                }
                
                success, user_id = context_manager.create_user_context(user_data)
                if success:
                    success, session_id = context_manager.start_user_session(user_id)
                    if success:
                        st.session_state.user_context = {
                            'user_id': user_id,
                            'session_id': session_id,
                            'school': selected_school,
                            'role': selected_role
                        }
                        st.success(f"✅ Profile set: {selected_role} at {selected_school}")
                    else:
                        st.error("Failed to start session")
                else:
                    st.error("Failed to create user context")
        
    # Display current profile
    if st.session_state.user_context:
        st.markdown("### 👤 Current Profile")
        st.write(f"**School:** {st.session_state.user_context['school']}")
        st.write(f"**Role:** {st.session_state.user_context['role']}")
        
        if st.button("🗑️ Clear Profile"):
            from context.user_context import UserContextManager
            context_manager = UserContextManager()
            context_manager.end_user_session(st.session_state.user_context['session_id'])
            st.session_state.user_context = None
            st.session_state.school_selected = None
            st.session_state.role_selected = None
            st.success("Profile cleared")
    
    # About section
    with st.expander("📚 About Husky AI"):
        st.markdown("""
        **Husky AI** is the official FUSD chatbot that provides:
        
        - 🏫 School-specific information
        - 📚 Academic policies and requirements
        - 🗓️ Event calendars and schedules
        - 🏆 Extracurricular activities
        - 📞 Contact information
        
        All information is sourced from official FUSD documents and policies.
        """)

# Main chat interface
st.markdown("### 💬 Chat")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])
            if "citations" in message:
                for citation in message["citations"]:
                    st.markdown(f"""
                    <div class="citation">
                    📄 Source: {citation['school_name']} - <a href="{citation['source_url']}" target="_blank">View Source</a> (Confidence: {citation['confidence']:.2f})
                    </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask about FUSD policies, schedules, or information..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Thinking...")

        try:
            # Single powerful RAG pipeline: hybrid retrieval (dense + BM25),
            # school routing, cross-encoder reranking, grounded LLM answer
            from backend.app.services.search_service import run_search

            # UI school picker biases retrieval when the question
            # doesn't name a school explicitly
            hint_sid = dict(school_options).get(selected_school_label)

            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[-6:]
                if m["role"] in ("user", "assistant")
                and "Error" not in m["content"][:20]
            ]

            result = run_search(prompt, history, school_hint=hint_sid)
            answer = result["answer"]
            sources = result.get("sources", [])

            message_placeholder.markdown(answer)

            if sources:
                source_line = "  ".join(
                    f"[{s.replace('https://fremontunified.org', '') or '/'}]"
                    f"({s})" for s in sources
                )
                st.markdown(f"📚 **Sources:** {source_line}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })

        except Exception as e:
            message_placeholder.markdown(f"❌ Error: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Error processing request: {str(e)}"
            })

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🐺 Husky AI - Official FUSD Chatbot | Powered by Streamlit</p>
        <p>All information sourced from official FUSD documents</p>
    </div>
""", unsafe_allow_html=True)
