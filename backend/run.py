import os

from dotenv import load_dotenv
load_dotenv()

from app import app


if __name__ == "__main__":
    # Allow overriding port via environment; default to Flask's usual 5000 so it matches the frontend default.
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
