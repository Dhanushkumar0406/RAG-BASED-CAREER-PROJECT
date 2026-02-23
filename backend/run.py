import os

from app import app


if __name__ == "__main__":
    # Allow overriding port via environment; default to 9000 for this project.
    port = int(os.getenv("PORT", "9000"))
    app.run(host="0.0.0.0", port=port, debug=True)
