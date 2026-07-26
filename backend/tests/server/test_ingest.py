"""Startup ingest of the /data markdown archives into the DB."""

import json


def test_weeks_lists_archive_weeks(archive_client):
    resp = archive_client.get("/artifacts/weeks")
    assert resp.status_code == 200
    weeks = {w["week"] for w in json.loads(resp.data)["weeks"]}
    for expected in ("2026-W22", "2026-W25", "2026-W28", "2026-W29"):
        assert expected in weeks


def test_archive_w25_has_all_cards(archive_client):
    resp = archive_client.get("/artifacts/archive?stem=W25")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    for agent in ("almanac", "macro", "technical", "evidence"):
        assert data[agent] is not None, f"missing {agent} card"
    assert data["llmComparison"] is not None
    assert data["llmComparison"]["models"]
    assert data["humanScoreReport"] is not None
    assert data["humanScoreReport"]["total"] == 2


def test_ingest_is_idempotent(archive_app):
    """A second ingest pass must not duplicate rows (upsert by natural key)."""
    from server.db import repository as repo
    from server.db.context import db_session
    from server.db.ingest import ingest_data_dir

    with archive_app.app_context():
        with db_session() as session:
            before = len(repo.list_runs(session, source="archive"))
        ingest_data_dir()  # run again
        with db_session() as session:
            after = len(repo.list_runs(session, source="archive"))
    assert before == after
