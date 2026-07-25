"""Export: regenerate markdown artifacts from the DB (never write to real /data)."""

import json


def test_post_export_stem_no_write(archive_client):
    resp = archive_client.post("/export", json={"stem": "W25", "write": False})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["week"] == "W25"
    assert data["written"] == []  # write=False -> nothing written to disk
    agents = {a["agent_type"] for a in data["artifacts"]}
    assert agents == {"almanac", "macro", "technical", "evidence"}
    for art in data["artifacts"]:
        assert art["markdown"].strip()


def test_post_export_missing_run(archive_client):
    resp = archive_client.post("/export", json={"stem": "W99", "write": False})
    assert resp.status_code == 404


def test_post_export_requires_target(archive_client):
    resp = archive_client.post("/export", json={})
    assert resp.status_code == 400


def test_write_artifacts_to_tmp(archive_app, tmp_path):
    from server.db import export, repository as repo
    from server.db.context import db_session

    with archive_app.app_context():
        with db_session() as session:
            run = repo.get_archive_run(session, "W25")
            assert run is not None
            artifacts = export.build_run_artifacts(session, run)
            written = export.write_artifacts(artifacts, data_dir=tmp_path)

    names = {p.rsplit("/", 1)[-1] for p in written}
    assert "almanac_agent_W25.md" in names
    assert "macro_agent_W25.md" in names
    assert "technical_agent_W25.md" in names
    assert "actuals_W25.md" in names
    for agent in ("almanac", "macro", "technical", "evidence"):
        assert (tmp_path / agent).is_dir()
