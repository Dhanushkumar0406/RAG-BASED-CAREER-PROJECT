import os
from typing import Tuple

import openai

# Default ChatGPT model; override via OPENAI_MODEL.
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def generate_response(context: str, question: str, model: str | None = None) -> Tuple[str, str]:
    """
    Given retrieved context and user question, produce a grounded answer using OpenAI Chat Completions.

    Returns:
        answer (str), used_model (str)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment.")

    client = openai.OpenAI(api_key=api_key)
    model_name = model or DEFAULT_MODEL
    prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional career assistant. "
                        "Use only the provided context to answer. "
                        "If the context is insufficient, say so briefly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        answer = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        answer = f"LLM error: {exc}"

    return answer, model_name


__all__ = ["generate_response"]
