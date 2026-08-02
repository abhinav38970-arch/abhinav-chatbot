#!/usr/bin/env python3
"""
Husky AI Streamlit Frontend
Modern chat interface for Washington High School AI Assistant
"""

import sys
from pathlib import Path

# Add backend to Python path to import directly
backend_path = str(Path(__file__).parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import streamlit as st
import requests
from datetime import datetime

# Import backend components directly for potential future use
try:
    from app.main import app as fastapi_app
    from app.routers.search_router import router as search_router
except ImportError as e:
    st.error(f"Backend import failed: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Husky AI - Washington High School",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #080d1a 0%, #0b1120 100%);
        color: #c8d4e8;
    }
    
    .chat-container {
        background: rgba(13, 22, 40, 0.8);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .ai-message {
        background: rgba(255, 102, 0, 0.1);
        border-left: 3px solid #ff6600;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .user-message {
        background: rgba(24, 32, 56, 0.8);
        border-right: 3px solid #182038;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .source-tag {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 5px 15px;
        display: inline-block;
        margin: 5px;
        font-size: 12px;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #0b1120 0%, #0d1628 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

# Display chat messages
def display_chat_messages():
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(f'<div class="ai-message">{message["content"]}</div>', unsafe_allow_html=True)
                if "sources" in message and message["sources"]:
                    sources_html = " ".join([
                        f'<span class="source-tag">🔗 {source}</span>'
                        for source in message["sources"]
                    ])
                    st.markdown(f'<div style="margin-top: 10px;">{sources_html}</div>', unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)

# Call backend API
def call_backend_api(query: str):
    """Call the FastAPI backend /ask endpoint"""
    try:
        response = requests.post(
            "http://localhost:8000/ask",
            json={"query": query, "history": st.session_state.chat_history},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"answer": f"Error connecting to backend: {str(e)}", "sources": []}

# Main app
def main():
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🐾 Husky AI")
        st.markdown("### Washington High School")
        st.markdown("---")
        
        st.markdown("""
        **Features:**
        - 🔍 Hybrid Search (FAISS + BM25)
        - 🧠 FlashRank Reranking
        - 📚 School Database Access
        - 💬 Conversation History
        """)
        
        st.markdown("---")
        st.markdown("""
        **Quick Questions:**
        - What's today's schedule?
        - When does lunch start?
        - What clubs are available?
        - Who do I contact about...?
        """)
        
        # Current time
        current_time = datetime.now().strftime("%I:%M %p")
        st.markdown(f"""
        ---
        **Status:** Online 🟢
        **Time:** {current_time}
        """)
    
    # Main chat area
    st.title("🐾 Husky AI - Washington High School Assistant")
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask anything about Washington High School..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
        
        # Get response from backend
        with st.spinner("🤖 Thinking..."):
            response = call_backend_api(prompt)
        
        # Add assistant response
        assistant_response = {
            "role": "assistant",
            "content": response.get("answer", "Sorry, I couldn't find that information."),
            "sources": response.get("sources", [])
        }
        
        st.session_state.messages.append(assistant_response)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": assistant_response["content"]
        })
        
        # Limit chat history to last 10 messages
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]
        
        # Re-display messages to show the new one
        display_chat_messages()

if __name__ == "__main__":
    main()