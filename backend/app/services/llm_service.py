import os
from typing import List, Tuple, Dict

import openai

# Default ChatGPT model; override via OPENAI_MODEL.
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

PERSONA_PRESETS = {
    "concise_career_coach": "You are a concise career coach. Give short, actionable answers in bullet points.",
    "detailed_analyst": "You are an analytical career advisor. Provide structured, detailed answers with reasoning.",
}


def _format_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Normalize chat history for the API (keep last 8 messages)."""
    allowed_roles = {"user", "assistant"}
    messages = []
    for m in history or []:
        role = m.get("role")
        if role not in allowed_roles:
            continue
        content = (m.get("text") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    return messages[-8:]


def generate_response(
    context: str,
    question: str,
    history: List[Dict[str, str]] | None = None,
    persona: str | None = None,
    model: str | None = None,
) -> Tuple[str, str]:
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
    persona_text = PERSONA_PRESETS.get(persona or "", PERSONA_PRESETS["concise_career_coach"])
    messages = [
        {
            "role": "system",
            "content": (
                f"{persona_text} "
                "Use ONLY the provided context to answer. "
                "If context is insufficient, reply exactly: \"I don't have enough information in the data to answer that.\" "
                "Respond in bullet points, <=120 words. "
                "Do not invent company names, salaries, or locations absent from the context."
            ),
        }
    ]
    messages.extend(_format_history(history))
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}",
        }
    )

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
        )
        answer = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        answer = f"LLM error: {exc}"

    return answer, model_name


__all__ = ["generate_response"]
