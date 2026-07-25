"""Bind the SQLite store to a Flask app and expose a per-request session."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from flask import Flask, current_app
from sqlalchemy.orm import Session

from server.db.engine import init_db, make_engine, make_session_factory

_FACTORY_KEY = "db_session_factory"
_ENGINE_KEY = "db_engine"


def init_app_db(app: Flask, db_url: str) -> None:
    """Create the engine, ensure the schema exists, and register both on the app."""
    engine = make_engine(db_url)
    init_db(engine)
    app.extensions[_ENGINE_KEY] = engine
    app.extensions[_FACTORY_KEY] = make_session_factory(engine)


@contextmanager
def db_session() -> Iterator[Session]:
    """Transactional session bound to the current app: commit/rollback/close."""
    factory = current_app.extensions[_FACTORY_KEY]
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
