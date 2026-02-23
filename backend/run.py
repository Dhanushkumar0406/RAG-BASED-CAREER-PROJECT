from app import app


if __name__ == "__main__":
    # Enable debug for local development; disable or set via env in prod.
    app.run(host="0.0.0.0", port=5000, debug=True)
