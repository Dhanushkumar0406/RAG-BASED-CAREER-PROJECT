import os
from typing import Tuple

import google.generativeai as genai

# Default model; override via env GEMINI_MODEL
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def generate_response(context: str, question: str, model: str | None = None) -> Tuple[str, str]:
    """
    Given retrieved context and user question, produce a grounded answer.

    Returns:
        answer (str), used_model (str)
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set in environment.")

    genai.configure(api_key=api_key)
    model_name = model or DEFAULT_MODEL

    system_prompt = (
        "You are a professional career assistant. "
        "Use only the provided context to answer. "
        "If the context is insufficient, say so briefly."
    )
    user_content = f"Context:\n{context}\n\nQuestion:\n{question}"

    try:
        gemini = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )
        resp = gemini.generate_content(user_content)
        answer = resp.text.strip() if resp.text else ""
    except Exception as exc:
        answer = f"LLM error: {exc}"

    return answer, model_name


__all__ = ["generate_response"]
