"""Server runtime

Reads server.toml (see server/config.py) for the LLM model registry offered
by the /stages/llm endpoint. Edit that file to add/remove models.

Usage:
    uv run python run_server.py
"""


from server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
