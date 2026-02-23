import os
from typing import Tuple

from openai import OpenAI

# Default lightweight model; override via env OPENAI_MODEL
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment.")
    return OpenAI(api_key=api_key)


def generate_response(context: str, question: str, model: str | None = None) -> Tuple[str, str]:
    """
    Given retrieved context and user question, produce a grounded answer.

    Returns:
        answer (str), used_model (str)
    """
    model_name = model or DEFAULT_MODEL
    client = _client()

    system_prompt = (
        "You are a professional career assistant. "
        "Use only the provided context to answer. "
        "If the context is insufficient, say so briefly."
    )
    user_content = f"Context:\n{context}\n\nQuestion:\n{question}"

    resp = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    content = resp.choices[0].message.content
    answer = content.strip() if content else ""
    return answer, model_name


__all__ = ["generate_response"]
