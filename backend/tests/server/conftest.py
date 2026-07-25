"""Shared fixtures for the server test suite.

Every app in these tests is built with an **isolated temp-file SQLite DB** and
``load_file_data=False`` by default, so tests never touch the real
``data/predictions.db`` nor auto-ingest the ``/data`` markdown archives.

A temp *file* (not ``:memory:``) is used so the same schema/rows survive across
the multiple connections a single request may open.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import pytest
from flask import Flask

from agents.io import week_stem
from server import create_app
from server.db import repository as repo
from server.db.context import db_session


def _make_app(tmp_path, *, load_file_data: bool, name: str = "test.db") -> Flask:
    db_url = f"sqlite:///{tmp_path / name}"
    app = create_app(db_url, load_file_data=load_file_data)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def app(tmp_path) -> Flask:
    """Isolated app with an empty DB (no /data ingest)."""
    return _make_app(tmp_path, load_file_data=False)


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def archive_app(tmp_path) -> Flask:
    """Isolated app that has ingested the real /data markdown archives."""
    return _make_app(tmp_path, load_file_data=True, name="archive.db")


@pytest.fixture
def archive_client(archive_app):
    with archive_app.test_client() as c:
        yield c


# --- seeding helpers ---------------------------------------------------------


@contextmanager
def app_session(app: Flask) -> Iterator:
    """Open an app context + a committing db_session for seeding."""
    with app.app_context():
        with db_session() as session:
            yield session


def seed_agent_output(
    app: Flask,
    *,
    run_id: str,
    prediction_date: date,
    agent_type: str,
    payload: dict,
    horizon_days: int | None = 7,
) -> None:
    """Insert a runtime agent output (creating its run) into the app's DB."""
    with app_session(app) as session:
        run = repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=week_stem(prediction_date),
        )
        repo.upsert_agent_output(session, run, agent_type, payload)


def seed_llm_output(
    app: Flask,
    *,
    run_id: str,
    prediction_date: date,
    model_slug: str,
    payload: dict,
    horizon_days: int | None = 7,
) -> None:
    with app_session(app) as session:
        run = repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=week_stem(prediction_date),
        )
        repo.upsert_llm_output(session, run, model_slug, payload)


def seed_runtime_run(
    app: Flask,
    *,
    run_id: str,
    prediction_date: date,
    horizon_days: int | None = 7,
) -> None:
    """Create a bare runtime run (no agent outputs)."""
    with app_session(app) as session:
        repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=week_stem(prediction_date),
        )
