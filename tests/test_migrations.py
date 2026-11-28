"""Tests for database migrations."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from calorhost.app_config import AppConfig
from calorhost.food.domain import NUTRIENT_DEFINITIONS
from calorhost.food.orm_models import NutrientRow, UserRow

app_config = AppConfig()


def test_upgrade_creates_schema_and_seeds_reference_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Upgrade creates the food schema and its default user and nutrients."""
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    migration_config = AlembicConfig()
    migration_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[1] / "src" / "calorhost" / "migrations"),
    )

    command.upgrade(migration_config, "head")

    engine = create_engine(database_url)
    try:
        assert {
            "users",
            "nutrients",
            "foods",
            "food_nutrition_bases",
            "food_nutrient_values",
            "alembic_version",
        } <= set(inspect(engine).get_table_names())

        with Session(engine) as session:
            users = session.scalars(select(UserRow)).all()
            nutrients = session.scalars(select(NutrientRow).order_by(NutrientRow.display_order)).all()

        assert [user.id for user in users] == [app_config.default_user_id]
        assert [(nutrient.code, nutrient.name, nutrient.canonical_unit) for nutrient in nutrients] == [
            (definition.code.value, definition.name, definition.canonical_unit) for definition in NUTRIENT_DEFINITIONS
        ]
    finally:
        engine.dispose()
