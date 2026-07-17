from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from server.artifacts import artifacts_bp
    from server.calibration import calibration_bp
    from server.stages import stages_bp

    app.register_blueprint(stages_bp)
    app.register_blueprint(artifacts_bp)
    app.register_blueprint(calibration_bp)

    return app
