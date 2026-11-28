"""Command-line database migration entry point."""

from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig

from .app_config import AppConfig

app_config = AppConfig()


def run() -> None:
    """Upgrade the database to the latest schema revision."""
    migration_config = AlembicConfig()
    migration_config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    migration_config.set_main_option("sqlalchemy.url", app_config.database_url.replace("%", "%%"))
    command.upgrade(migration_config, "head")
