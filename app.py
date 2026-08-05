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

# Custom CSS - 🔧 TASK 3: COMPLETELY REDESIGNED UI
st.markdown("""
<style>
    /* Modern dark theme with Washington High School branding */
    .stApp {
        background: linear-gradient(135deg, #080d1a 0%, #0b1120 100%);
        color: #c8d4e8;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    
    /* Chat container styling */
    .chat-container {
        background: rgba(13, 22, 40, 0.8);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    
    /* AI message bubbles - modern design */
    .ai-message {
        background: linear-gradient(135deg, rgba(255, 102, 0, 0.08) 0%, rgba(255, 102, 0, 0.03) 100%);
        border-left: 3px solid #ff6600;
        padding: 18px 22px;
        border-radius: 12px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(255, 102, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .ai-message:hover {
        box-shadow: 0 4px 12px rgba(255, 102, 0, 0.15);
        transform: translateY(-1px);
    }
    
    /* User message bubbles - modern design */
    .user-message {
        background: rgba(24, 32, 56, 0.8);
        border-right: 3px solid #182038;
        padding: 18px 22px;
        border-radius: 12px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .user-message:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        transform: translateY(-1px);
    }
    
    /* Source links styling */
    .source-link {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 6px 16px;
        display: inline-block;
        margin: 6px 4px;
        font-size: 13px;
        color: #ff6600;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    
    .source-link:hover {
        background: rgba(255, 102, 0, 0.15);
        border-color: rgba(255, 102, 0, 0.3);
        transform: translateY(-1px);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #0b1120 0%, #0d1628 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Header styling */
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Subtitle styling */
    .header-subtitle {
        color: #ff6600;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    
    /* Chat input area styling */
    .stChatInput {
        background: rgba(18, 25, 42, 0.9);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Status indicators */
    .status-online {
        color: #4ade80;
        font-weight: 600;
    }
    
    .status-offline {
        color: #f87171;
        font-weight: 600;
    }
    
    /* Feature list styling */
    .feature-list {
        list-style-type: none;
        padding-left: 0;
    }
    
    .feature-list li {
        padding: 8px 0;
        position: relative;
        padding-left: 24px;
    }
    
    .feature-list li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #ff6600;
        font-weight: bold;
    }
    
    /* Quick questions styling */
    .quick-questions {
        background: rgba(18, 25, 42, 0.6);
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
    }
    
    /* Time display */
    .time-display {
        color: #94a3b8;
        font-size: 0.9rem;
        text-align: center;
        padding: 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .ai-message, .user-message {
            padding: 14px 16px;
            font-size: 0.95rem;
        }
        
        .header-title {
            font-size: 1.8rem;
        }
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 102, 0, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 102, 0, 0.5);
    }
    
    /* Animation for chat messages */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .ai-message, .user-message {
        animation: fadeIn 0.3s ease-out;
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
                    # 🔧 TASK 2: FIXED - Use clickable links instead of plain text
                    clickable_sources = make_links_clickable(message["sources"])
                    if clickable_sources:
                        sources_markdown = " | ".join(clickable_sources)
                        st.markdown(f"**Sources:** {sources_markdown}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)

# 🔧 TASK 2: FIXED - Make source links clickable
# Convert plain text URLs into proper Markdown hyperlinks
def make_links_clickable(sources):
    """Convert plain text URLs into clickable Markdown links"""
    clickable_links = []
    for source in sources:
        if source and source.strip():
            # Clean up the URL
            clean_url = source.strip()
            # Remove any existing markdown formatting
            clean_url = clean_url.replace("[", "").replace("]", "")
            # Create clickable link with emoji
            display_text = "🔗 Official Link"
            clickable_link = f"[{display_text}]({clean_url})"
            clickable_links.append(clickable_link)
    return clickable_links

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
    
    # Sidebar - 🔧 TASK 3: REDESIGNED SIDEBAR
    with st.sidebar:
        st.markdown('<div class="header-title">🐾 Husky AI</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 1rem;">Washington High School</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # API Status with better styling
        if "Loaded Successfully" in api_key_status:
            st.markdown(f'<div style="color: #4ade80; font-weight: 600; margin-bottom: 1rem;">API Status: {api_key_status}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color: #f87171; font-weight: 600; margin-bottom: 1rem;">API Status: {api_key_status}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Features with checkmarks
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <strong>Features:</strong>
            <ul class="feature-list">
                <li>Hybrid Search (FAISS + BM25)</li>
                <li>FlashRank Reranking</li>
                <li>School Database Access</li>
                <li>Conversation History</li>
                <li>Local Execution</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick Questions with better styling
        st.markdown("""
        <div class="quick-questions">
            <strong>Quick Questions:</strong>
            <ul style="margin-top: 0.5rem; padding-left: 20px;">
                <li>What's today's schedule?</li>
                <li>When does lunch start?</li>
                <li>What clubs are available?</li>
                <li>Who do I contact about...?</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Time display with styling
        current_time = datetime.now().strftime("%I:%M %p")
        st.markdown(f"""
        <div class="time-display">
            <strong>Status:</strong> Online 🟢<br>
            <strong>Mode:</strong> Local Execution<br>
            <strong>Time:</strong> {current_time}
        </div>
        """, unsafe_allow_html=True)
    
    # Main chat area - 🔧 TASK 3: REDESIGNED HEADER
    st.markdown('<div class="header-title">🐾 Husky AI - Washington High School Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">🚀 Now running entirely locally - no server required!</div>', unsafe_allow_html=True)
    
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
