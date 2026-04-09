# backend/app/services/llm_service.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant" 

def generate_answer(query: str, context: str, history: list = None, model_type=None):
    if history is None:
        history = []

    # REFINED SYSTEM PROMPT FOR CLEAN, ULTRA-CONCISE STRUCTURE
    system_msg = (
        "You are 'Husky AI', the official professional assistant for Washington High School (WHS).\n\n"
        "FORMATTING & STYLE RULES:\n"
        "1. VISUAL STRUCTURE: Use clear, organized lines. Use dashes (-) for bullet points.\n"
        "2. NO SPECIAL FORMATTING: Do not use bold text (**), italics, or ALL CAPS for emphasis.\n"
        "3. FAILED SEARCH: If the information is missing, respond with exactly: 'Unfortunately, I don't have the details about the question you asked me; maybe the pages attached in the links below may help you.'\n"
        "4. BREVITY: Be extremely concise. Deliver facts immediately without introductory filler or conversational fluff. Aim for a maximum of 2 sentences or a short list.\n"
        "5. TONE: Professional and dignified.\n"
        "6. CLOSING: Every successful answer must end with the sentence: 'If what I told you didn't answer your question the links below will be helpful.'"
    )
    
    messages = [{"role": "system", "content": system_msg}]

    for msg in history:
        messages.append(msg)

    prompt = f"""
CONTEXT DATA:
{context}

USER QUESTION: {query}

TASK: Provide an easy-to-read, ultra-concise structured response using simple text.
ANSWER:
"""
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1, 
        )
        return response.choices[0].message.content
    except Exception as e:
        return "A technical error has occurred."