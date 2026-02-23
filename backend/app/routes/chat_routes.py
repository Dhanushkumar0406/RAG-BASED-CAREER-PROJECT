from flask import Blueprint, jsonify, request

from app.services.rag_pipeline import RagPipeline
from app.services.llm_service import generate_response

chat_bp = Blueprint("chat", __name__)

# Lazily initialized singletons to avoid reloading the model on each request.
_pipeline = None


def _get_pipeline() -> RagPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RagPipeline()
    return _pipeline


@chat_bp.route("/chat", methods=["POST"])
def chat():
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
