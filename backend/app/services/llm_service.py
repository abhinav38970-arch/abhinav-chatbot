import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MODEL = "llama-3.1-8b-instant" 

# 🛠️ THE FIX: We kept 'model_type=None' to ensure compatibility with search_service.
def generate_answer(query: str, context: str, history: list = None, model_type=None):
    """
    Sends query + retrieved context + conversation history to LLM.
    'history' allows the AI to remember previous turns.
    """
    if history is None:
        history = []

    if not context.strip():
        return "Information regarding this query is currently unavailable in the Washington High School database."

    # Dynamically grab fresh key from environment on every request
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    # 1. THE REFINED SYSTEM PROMPT: Professional, Dignified, and Filtered.
    system_msg = (
        "You are 'Husky AI', the official professional assistant for Washington High School (WHS).\n\n"
        "STRICT FILTRATION & STYLE RULES:\n"
        "1. WASHINGTON ONLY: You must filter the district-wide data to find information pertaining ONLY to Washington High School. Do not mention individuals or policies from other schools (e.g., Kennedy, Irvington).\n"
        "2. PROFESSIONAL TONE: Maintain a dignified, polite, and formal tone. Avoid being overly friendly or casual.\n"
        "3. NO BOLDING: Do not use any bold text (no double asterisks). Provide responses in plain, clean text.\n"
        "4. CONCISE SUMMARIES: Provide a direct answer. The response should be 1 to 3 sentences usually, and must NEVER exceed 5 sentences.\n"
        "5. CLEAN FORMATTING: Do not use symbols like '*' or '+'. Use plain text or standard numbered lists (1. 2. 3.) only when necessary.\n"
        "6. SOURCE OF TRUTH: Use only the provided context. If the specific data for Washington High is not found, state that the information is not available in current records."
    )
    
    messages = [
        {"role": "system", "content": system_msg}
    ]

    # 2. Add History
    for msg in history:
        messages.append(msg)

    # 3. Final Prompt
    prompt = f"""
SCHOOL DISTRICT DATA:
{context}

USER QUESTION: {query}

TASK:
1. Identify and extract information exclusively for Washington High School.
2. Provide a professional and polite summary.
3. Maximum length: 4-5 sentences.
4. Do not use bold text or special bullet symbols.

ANSWER:
"""
    messages.append({"role": "user", "content": prompt})

    try:
        # Temperature 0.1 ensures the model remains literal and professional.
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"A technical error has occurred: {str(e)}"
