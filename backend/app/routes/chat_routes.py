from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, jsonify, request

if TYPE_CHECKING:
    from app.services.rag_pipeline import RagPipeline

chat_bp = Blueprint("chat", __name__)

# Lazily initialized singletons to avoid reloading the model on each request.
_pipeline = None


def _get_pipeline() -> RagPipeline:
    global _pipeline
    if _pipeline is None:
        # Heavy imports happen only when the first chat request arrives, keeping health checks snappy.
        from app.services.rag_pipeline import RagPipeline
        _pipeline = RagPipeline()
    return _pipeline


@chat_bp.route("/chat", methods=["POST"])
def chat():
    # Import here to avoid pulling genai stack unless we actually need it.
    from app.services.llm_service import generate_response
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    pipeline = _get_pipeline()
    try:
        context_text, hits = pipeline.retrieve(question)
        answer, model_used = generate_response(context_text, question)
    except Exception as exc:  # fallback so frontend gets a friendly message
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "answer": answer,
            "model": model_used,
            "hits": hits,
        }
    )
