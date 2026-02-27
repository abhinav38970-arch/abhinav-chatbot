import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "llama-3.1-8b-instant"  # free + strong


def generate_answer(query: str, context: str):
    """
    Sends query + retrieved context to LLM
    """

    prompt = f"""
You are a helpful school AI assistant.

Answer the user's question using ONLY the information provided below.

If the answer is not in the context, say:
"I couldn't find that information in the school database."

Context:
{context}

Question:
{query}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content