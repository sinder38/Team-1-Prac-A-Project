from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from server.stages import stages_bp
    from server.artifacts import artifacts_bp

    app.register_blueprint(stages_bp)
    app.register_blueprint(artifacts_bp)

    return app
