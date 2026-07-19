from flask import Blueprint, jsonify

from server.stages import CONFIG

models_bp = Blueprint("models", __name__, url_prefix="/config")


@models_bp.route("/models", methods=["GET"])
def get_models():
    return jsonify({
        "models": [
            {"key": m.slug, "name": m.name, "provider": m.provider}
            for m in CONFIG.llm.models
        ]
    })
