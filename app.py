#!/usr/bin/env python3
"""
Husky AI Streamlit Frontend - Standalone Version
Modern chat interface for Washington High School AI Assistant
Now runs entirely locally without FastAPI server dependency
"""

import sys
from pathlib import Path
import streamlit as st
import os

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Husky AI - Washington High School",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Automatically map Streamlit Secrets to environment variables for Groq with visual feedback
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
        api_key_status = "Loaded Successfully 🟢"
    else:
        api_key_status = "Not Found in Secrets 🔴"
except Exception as e:
    api_key_status = f"Error reading secrets: {e}"

# Add project root directory to Python path so 'backend.app' imports work correctly
root_path = str(Path(__file__).parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from datetime import datetime

# Import backend components using absolute package paths
try:
    from backend.app.services.search_service import run_search
    from backend.app.services.llm_service import generate_answer
    from backend.app.retrieval.search import search as vector_search
    from backend.app.retrieval.vector_store import VectorStore
    from backend.app.retrieval.embedder import embed_text
    import numpy as np
    print("✅ Backend components imported successfully")
except ImportError as e:
    st.error(f"Backend import failed: {e}")
    st.stop()

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

# Direct local function call to backend logic
def call_local_backend(query: str):
    """
    Call backend logic directly without HTTP requests
    """
    try:
        result = run_search(query, st.session_state.chat_history)
        return {
            "answer": result.get("answer", "Sorry, I couldn't find that information."),
            "sources": result.get("sources", [])
        }
    except Exception as e:
        return {
            "answer": f"An error occurred: {str(e)}",
            "sources": []
        }

# Main app
def main():
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🐾 Husky AI")
        st.markdown("### Washington High School")
        st.markdown("---")
        
        st.markdown(f"""
        **API Status:** {api_key_status}
        """)
        st.markdown("---")
        
        st.markdown("""
        **Features:**
        - 🔍 Hybrid Search (FAISS + BM25)
        - 🧠 FlashRank Reranking
        - 📚 School Database Access
        - 💬 Conversation History
        - ⚡ Local Execution (No Server Needed)
        """)
        
        st.markdown("---")
        st.markdown("""
        **Quick Questions:**
        - What's today's schedule?
        - When does lunch start?
        - What clubs are available?
        - Who do I contact about...?
        """)
        
        current_time = datetime.now().strftime("%I:%M %p")
        st.markdown(f"""
        ---
        **Status:** Online 🟢
        **Mode:** Local Execution
        **Time:** {current_time}
        """)
    
    # Main chat area
    st.title("🐾 Husky AI - Washington High School Assistant")
    st.markdown("""
    <div style="color: #ff6600; margin-bottom: 20px;">
    🚀 Now running entirely locally - no server required!
    </div>
    """, unsafe_allow_html=True)
    
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask anything about Washington High School..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
        
        with st.spinner("🤖 Thinking..."):
            response = call_local_backend(prompt)
        
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
        
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]
        
        display_chat_messages()

if __name__ == "__main__":
    main()
