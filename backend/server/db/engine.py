"""SQLAlchemy engine, session factory, and schema bootstrap.

SQLite is the single source of truth for server runtime data. The database
file lives at ``DB_PATH`` (``data/predictions.db``) unless overridden — tests
pass an in-memory or temp-file URL.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from agents.paths import DB_PATH
from server.db.models import Base

DEFAULT_DB_URL = f"sqlite:///{DB_PATH}"


def _enable_sqlite_fks(dbapi_connection, _connection_record) -> None:
    """SQLite ignores foreign keys unless the pragma is set per connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(db_url: str = DEFAULT_DB_URL) -> Engine:
    engine = create_engine(db_url, future=True)
    event.listen(engine, "connect", _enable_sqlite_fks)
    return engine


def init_db(engine: Engine) -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Transactional scope: commit on success, roll back on error."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
