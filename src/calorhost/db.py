"""Database engine and session setup."""

import sqlite3
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .app_config import AppConfig

app_config = AppConfig()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def create_database_engine(database_url: str) -> Engine:
    """Create an engine and enable SQLite foreign-key enforcement."""
    url = make_url(database_url)
    connect_args: dict[str, bool] = {}

    if url.get_backend_name() == "sqlite":
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False

    if url.get_backend_name() == "sqlite" and url.database in {None, ":memory:"}:
        engine = create_engine(database_url, connect_args=connect_args, poolclass=StaticPool)
    else:
        engine = create_engine(database_url, connect_args=connect_args)

    if url.get_backend_name() == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection: sqlite3.Connection, _record: object) -> None:
            """Enable SQLite foreign keys on each connection."""
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


@lru_cache
def get_engine() -> Engine:
    """Return the application database engine."""
    return create_database_engine(app_config.database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the application session factory."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Yield a database session for a request."""
    with get_session_factory()() as session:
        yield session
