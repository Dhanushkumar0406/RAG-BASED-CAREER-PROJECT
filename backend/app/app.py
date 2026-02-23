from flask import Flask
from flask_cors import CORS

from app.routes import chat_bp


def create_app() -> Flask:
    """Application factory returning a configured Flask app."""
    app = Flask(__name__)
    CORS(app)

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

    @app.route("/", methods=["GET"])
    def index():
        return {
            "status": "ok",
            "message": "Backend running.",
        }, 200

    # Register blueprints
    app.register_blueprint(chat_bp)

    return app


# Expose a default app instance for simple imports (e.g., run.py).
app = create_app()
