import os
import time
from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    RateLimitError,
    InternalServerError
)
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
    Includes exponential backoff retry (up to 3 attempts) for transient errors (429, 5xx, timeouts).
    Does NOT retry non-transient errors (e.g. 413 Payload Too Large, 400 Bad Request).
    """
    client = get_groq_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    max_retries = 3
    base_delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Calling Groq API with model: {model} (attempt {attempt}/{max_retries})")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content

        except (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError) as transient_err:
            if attempt == max_retries:
                logger.error(f"Groq API call failed after {max_retries} attempts: {transient_err}")
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Groq API transient error ({transient_err.__class__.__name__}). Retrying in {delay}s...")
            time.sleep(delay)

        except APIStatusError as status_err:
            status_code = getattr(status_err, "status_code", 0)
            if status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Groq API status error HTTP {status_code}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Groq API non-transient error HTTP {status_code}: {status_err}")
                raise

        except Exception as e:
            logger.error(f"Groq API unexpected error: {e}")
            raise


def test_groq_connection() -> dict:
    """Smoke test for Groq API."""
    try:
        res = call_groq(
            prompt="Respond with a short JSON string: {\"status\": \"ok\", \"message\": \"Groq operational\"}",
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
