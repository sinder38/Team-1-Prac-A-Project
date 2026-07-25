import os

from flask import Flask

from server.db.context import init_app_db
from server.db.engine import DEFAULT_DB_URL


def create_app(db_url: str | None = None, *, load_file_data: bool | None = None) -> Flask:
    app = Flask(__name__)

    # SQLite is the source of truth for runtime data. Tests pass an in-memory
    # URL; production falls back to data/predictions.db.
    resolved_db_url = db_url or os.environ.get("PREDICTIONS_DB_URL") or DEFAULT_DB_URL
    init_app_db(app, resolved_db_url)

    # Optionally seed the DB from the /data markdown archives on startup. The
    # config flag can be overridden per-call (tests pass load_file_data=False).
    from server.stages import CONFIG

    do_ingest = (
        CONFIG.database.load_file_data if load_file_data is None else load_file_data
    )
    if do_ingest:
        from server.db.ingest import ingest_data_dir

        with app.app_context():
            ingest_data_dir()

    from server.artifacts import artifacts_bp
    from server.calibration import calibration_bp
    from server.export_routes import export_bp
    from server.market import market_bp
    from server.model_routes import models_bp
    from server.stages import stages_bp

    app.register_blueprint(stages_bp)
    app.register_blueprint(artifacts_bp)
    app.register_blueprint(calibration_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(models_bp)

    return app
