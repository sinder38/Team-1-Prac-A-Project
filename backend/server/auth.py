"""Single-admin authentication for write operations."""

from secrets import compare_digest

from flask import Blueprint, Flask, current_app, jsonify, request, session

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

READ_METHODS = {"GET", "HEAD", "OPTIONS"}
PUBLIC_WRITE_ENDPOINTS = {"auth.login", "auth.logout"}


def init_auth(app: Flask) -> None:
    """Require an authenticated session for every operation that changes data."""

    @app.before_request
    def protect_write_operations():
        if request.method in READ_METHODS:
            return None
        if request.endpoint in PUBLIC_WRITE_ENDPOINTS:
            return None
        if not _auth_is_configured(app):
            return jsonify({"error": "Authentication is not configured."}), 503
        if not session.get("is_admin"):
            return jsonify({"error": "Authentication required."}), 401
        return None


@auth_bp.route("/status", methods=["GET"])
def status():
    configured = _auth_is_configured(current_app)
    authenticated = configured and bool(session.get("is_admin"))
    username = session.get("username") if authenticated else None
    return jsonify(
        {
            "authenticated": authenticated,
            "configured": configured,
            "username": username,
        }
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    app = current_app
    if not _auth_is_configured(app):
        return jsonify({"error": "Authentication is not configured."}), 503

    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required."}), 400

    expected_username = app.config["AUTH_USERNAME"]
    expected_password = app.config["AUTH_PASSWORD"]
    username_matches = compare_digest(username, expected_username)
    password_matches = compare_digest(password, expected_password)
    if not username_matches or not password_matches:
        session.clear()
        return jsonify({"error": "Invalid username or password."}), 401

    session.clear()
    session["is_admin"] = True
    session["username"] = username
    return jsonify({"authenticated": True, "username": username})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if _auth_is_configured(current_app):
        session.clear()
    return jsonify({"authenticated": False})


def _auth_is_configured(app: Flask) -> bool:
    return bool(
        app.config.get("AUTH_USERNAME")
        and app.config.get("AUTH_PASSWORD")
        and app.config.get("SECRET_KEY")
    )
