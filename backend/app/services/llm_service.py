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

    # 1. THE ENHANCED SYSTEM PROMPT: Professional, Context-Aware, and Intelligent
    system_msg = (
        "You are 'Husky AI', the official intelligent assistant for Washington High School (WHS).\n\n"
        "CORE PRINCIPLES:\n"
        "1. WASHINGTON-FOCUSED: Filter all information to be specific to Washington High School only.\n"
        "2. PROFESSIONAL EXCELLENCE: Maintain a polished, authoritative, and helpful tone.\n"
        "3. CONTEXTUAL INTELLIGENCE: Use the provided context wisely to answer accurately.\n"
        "4. PRECISION & CLARITY: Be concise yet comprehensive, providing complete answers.\n"
        "5. TRANSPARENT SOURCING: When possible, reference the source of your information.\n\n"
        "ADVANCED RESPONSE GUIDELINES:\n"
        "- Use natural language with proper grammar and punctuation\n"
        "- Structure answers logically with clear organization\n"
        "- Provide specific details when available (times, dates, locations)\n"
        "- If information is unavailable, state so clearly and professionally\n"
        "- Never fabricate or guess information - only use provided context\n"
        "- For complex questions, break answers into clear, numbered points\n"
        "- Maintain a helpful, service-oriented attitude\n"
        "- Adapt response length to question complexity (1-3 paragraphs max)\n"
        "- TEMPORAL CONTEXT: Be aware of the current school year and academic period\n"
    )
    
    messages = [
        {"role": "system", "content": system_msg}
    ]

    # 2. Add History for Context Continuity
    for msg in history:
        messages.append(msg)

    # 3. ENHANCED PROMPT ENGINEERING with Context Analysis
    prompt = f"""
📚 CONTEXTUAL KNOWLEDGE BASE:
{context}

🤔 USER INTENT ANALYSIS:
- Query: "{query}"
- Context Length: {len(context.split())} words
- Context Quality: {'High' if len(context) > 100 else 'Limited'}

🎯 INTELLIGENT RESPONSE TASK:
1. ANALYZE: Carefully examine the contextual knowledge base
2. EXTRACT: Identify the most relevant information for Washington High School
3. SYNTHESIZE: Create a professional, comprehensive response
4. STRUCTURE: Organize the answer logically with clear sections if needed
5. ENHANCE: Add value with insights, explanations, or helpful suggestions

📝 RESPONSE FORMAT GUIDE:
- Start with a direct answer to the main question
- Provide supporting details in a logical sequence
- Use complete sentences with proper grammar
- For lists, use: 1. First item, 2. Second item, 3. Third item
- End with a helpful closing or next steps if appropriate

💡 EXAMPLE QUALITY RESPONSE:
"The bell schedule for Washington High School follows a regular pattern on Mondays, Thursdays, and Fridays. Classes begin at 8:30 AM with Period 1 and conclude at 3:26 PM with Period 6. The schedule includes a morning break at 10:20 AM and lunch at 1:00 PM. For specific period times or special schedules, please refer to the school's official calendar or contact the main office."

🎓 YOUR INTELLIGENT RESPONSE:
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
