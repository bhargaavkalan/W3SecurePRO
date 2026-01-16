import os
from groq import Groq

def ask_ai(title, evidence):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "❌ GROQ_API_KEY not set. Run: export GROQ_API_KEY='your_key'"

    client = Groq(api_key=api_key)

    prompt = f"""
You are W3Secure AI Security Advisor.
Explain the security issue in SIMPLE language for a NON-TECHNICAL client.

Issue Title: {title}
Evidence: {evidence}

Return exactly in this format:

✅ Client Summary (2 lines)
✅ Why this is risky (1-2 lines)
✅ What we recommend (3 bullet points)
✅ Priority: High/Medium/Low
✅ Estimated Fix Time: Quick / 1 Day / 1 Week
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You generate client-friendly security mitigation guidance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Groq AI Error: {e}"
