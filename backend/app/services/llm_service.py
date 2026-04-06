import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq Client
# FIXED: Removed the hardcoded 'gsk_...' key. 
# It now looks only in your .env file for GROQ_API_KEY.
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "llama-3.1-8b-instant" 

def generate_answer(query: str, context: str, history: list = None):
    """
    Sends query + retrieved context + conversation history to LLM.
    'history' allows the AI to remember previous turns like '0 period'.
    """
    if history is None:
        history = []

    if not context.strip():
        return "I couldn't find any relevant information in the school database."

    # 1. Start with the System Prompt (The AI's "Personality")
    messages = [
        {"role": "system", "content": "You are a helpful school AI assistant for Washington High. Answer using ONLY the provided context. If the user corrects you, check the context again to see if they are right."}
    ]

    # 2. Add the Conversation History (The AI's "Memory")
    for msg in history:
        messages.append(msg)

    # 3. Add the current Question and the Context found in FAISS
    prompt = f"""
Answer the user's question using ONLY the context provided below.

Context:
{context}

Question:
{query}
"""
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {str(e)}"