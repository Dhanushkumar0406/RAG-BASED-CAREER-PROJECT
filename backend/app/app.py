from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    """Application factory returning a configured Flask app."""
    app = Flask(__name__)
    CORS(app)

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

    return app


# Expose a default app instance for simple imports (e.g., run.py).
app = create_app()
