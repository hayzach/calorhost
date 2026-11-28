"""Shared database and custom-food fixtures."""

from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from calorhost.app_config import AppConfig
from calorhost.db import Base, create_database_engine, get_session
from calorhost.food.domain import (
    NUTRIENT_DEFINITIONS,
    BasisKind,
    CustomFoodInput,
    NutrientAmount,
    NutrientCode,
    NutritionBasis,
)
from calorhost.food.orm_models import NutrientRow, UserRow
from calorhost.main import app

app_config = AppConfig()


@pytest.fixture
def test_session_factory() -> Iterator[sessionmaker[Session]]:
    """Create an isolated in-memory database with required reference data."""
    engine = create_database_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        session.add(UserRow(id=app_config.default_user_id))
        session.add_all(
            [
                NutrientRow(
                    code=definition.code.value,
                    name=definition.name,
                    canonical_unit=definition.canonical_unit,
                    display_order=definition.display_order,
                )
                for definition in NUTRIENT_DEFINITIONS
            ]
        )
        session.commit()
    yield session_factory
    engine.dispose()


@pytest.fixture
def custom_food_input() -> CustomFoodInput:
    """Return a valid per-100-g custom-food input."""
    return CustomFoodInput(
        name="Rolled oats",
        nutrition_bases=(
            NutritionBasis(
                kind=BasisKind.PER_100G,
                values=(
                    NutrientAmount(NutrientCode.ENERGY, Decimal("0")),
                    NutrientAmount(NutrientCode.PROTEIN, Decimal("13.2")),
                    NutrientAmount(NutrientCode.FAT, Decimal("6.5")),
                    NutrientAmount(NutrientCode.CARBOHYDRATES, Decimal("67.7")),
                ),
            ),
        ),
    )


@pytest.fixture
def client(test_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Create a test client connected to the isolated database."""

    def override_session() -> Iterator[Session]:
        """Yield a session from the fixture's database."""
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
