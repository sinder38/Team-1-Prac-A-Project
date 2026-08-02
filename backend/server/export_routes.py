"""POST /export — regenerate Markdown artifacts from the DB on request."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from core.io import week_stem
from server.db import export, repository as repo
from server.db.context import db_session
from server.utils import err

export_bp = Blueprint("export", __name__, url_prefix="/export")


@export_bp.route("", methods=["POST"])
def post_export():
    """Render (and optionally write) the .md artifacts for a run or archive week.

    Body: {"run_id": "..."} for a runtime run, or {"stem": "W25"} for an
    archive week. Optional {"write": false} to return content without writing
    files (defaults to writing under data/<agent>/).
    """
    try:
        body = request.get_json(force=True) or {}
    except BadRequest:
        return err("Invalid JSON body", 400)

    run_id = body.get("run_id")
    stem = body.get("stem")
    write = bool(body.get("write", True))
    if not run_id and not stem:
        return err("Provide either run_id or stem", 400)

    with db_session() as session:
        if run_id:
            run = repo.get_runtime_run(session, str(run_id))
        else:
            run = repo.get_archive_run(session, str(stem))
        if run is None:
            return err("No matching run found", 404)

        artifacts = export.build_run_artifacts(session, run)
        written = export.write_artifacts(artifacts) if write else []
        payload = {
            "run_id": run.run_id,
            "week": run.week_stem or week_stem(run.prediction_date),
            "written": written,
            "artifacts": [
                {
                    "agent_type": a["agent_type"],
                    "filename": a["filename"],
                    "markdown": a["markdown"],
                }
                for a in artifacts
            ],
        }
    return jsonify(payload), 200
