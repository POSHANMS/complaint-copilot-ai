import os
from groq import Groq
from app.core.config import settings
from app.core.logging import logger

# Note: Groq decommissioned gemma2-9b-it; llama-3.1-8b-instant is the active fast model
MODEL_GEMMA = "llama-3.1-8b-instant"
MODEL_LLAMA_HEAVY = "llama-3.3-70b-versatile"

def get_groq_client() -> Groq:
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "gsk_your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set or is using placeholder value.")
    return Groq(api_key=api_key)

def call_groq(prompt: str, system_prompt: str = "", model: str = MODEL_GEMMA, temperature: float = 0.1) -> str:
    """
    Central wrapper for all Groq API calls.
    Never call Groq SDK directly from node files.
    """
    client = get_groq_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    logger.info(f"Calling Groq API with model: {model}")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

def test_groq_connection() -> dict:
    """
    Smoke test to confirm connection to gemma2-9b-it works.
    """
    try:
        res = call_groq(
            prompt="Respond with a short JSON string: {\"status\": \"ok\", \"message\": \"Groq gemma2-9b-it operational\"}",
            system_prompt="You are a system health check assistant. Respond in strict JSON.",
            model=MODEL_GEMMA
        )
        return {"success": True, "response": res}
    except Exception as e:
        logger.error(f"Groq connection test failed: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("Testing Groq connection...")
    result = test_groq_connection()
    print("Result:", result)
