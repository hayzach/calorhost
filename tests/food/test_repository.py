"""Tests for SQLAlchemy food persistence."""

from dataclasses import replace
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from calorhost.app_config import AppConfig
from calorhost.food.domain import (
    AmountUnit,
    BasisKind,
    CustomFoodInput,
    Food,
    NutrientCode,
    ServingSize,
)
from calorhost.food.orm_models import FoodNutrientValueRow, FoodNutritionBasisRow
from calorhost.food.repository import SqlAlchemyFoodRepository

app_config = AppConfig()


def test_repository_preserves_zero_and_missing_nutrients(
    test_session_factory: sessionmaker[Session],
    custom_food_input: CustomFoodInput,
) -> None:
    """Persisted nutrient rows distinguish unknown values from known zeroes."""
    with test_session_factory() as session:
        repository = SqlAlchemyFoodRepository(session)
        food = Food.create_custom(app_config.default_user_id, custom_food_input)
        repository.save_custom_food(food)

        loaded_food = repository.get_custom_food(food.id, app_config.default_user_id)
        value_rows = session.scalars(select(FoodNutrientValueRow)).all()

    assert loaded_food is not None
    known_values = {item.nutrient: item.value for item in loaded_food.nutrition_bases[0].values}
    assert known_values[NutrientCode.ENERGY] == Decimal("0")
    assert known_values[NutrientCode.PROTEIN] == Decimal("13.2")
    assert NutrientCode.FIBER not in known_values
    assert len(value_rows) == 4


def test_repository_scopes_foods_to_the_owner(
    test_session_factory: sessionmaker[Session],
    custom_food_input: CustomFoodInput,
) -> None:
    """Only the owner can retrieve a custom food from the repository."""
    with test_session_factory() as session:
        repository = SqlAlchemyFoodRepository(session)
        food = repository.save_custom_food(Food.create_custom(app_config.default_user_id, custom_food_input))

        assert repository.get_custom_food(food.id, "other-user") is None
        assert repository.list_custom_foods("other-user") == []


def test_repository_replaces_basis_values_on_update(
    test_session_factory: sessionmaker[Session],
    custom_food_input: CustomFoodInput,
) -> None:
    """Updating a food removes its old basis values."""
    with test_session_factory() as session:
        repository = SqlAlchemyFoodRepository(session)
        original = Food.create_custom(app_config.default_user_id, custom_food_input)
        repository.save_custom_food(original)
        replacement_input = CustomFoodInput(
            name="Updated oats",
            nutrition_bases=(custom_food_input.nutrition_bases[0],),
        )
        updated = Food.create_custom(app_config.default_user_id, replacement_input, food_id=original.id)
        repository.save_custom_food(updated)

        basis_count = session.scalar(select(func.count()).select_from(FoodNutritionBasisRow))
        value_count = session.scalar(select(func.count()).select_from(FoodNutrientValueRow))
        loaded_food = repository.get_custom_food(original.id, app_config.default_user_id)

    assert basis_count == 1
    assert value_count == 4
    assert loaded_food is not None
    assert loaded_food.name == "Updated oats"


def test_repository_saves_per_serving_nutrition_and_conversion(
    test_session_factory: sessionmaker[Session],
    custom_food_input: CustomFoodInput,
) -> None:
    """Per-serving nutrition and its known gram equivalent survive persistence."""
    serving_basis = replace(
        custom_food_input.nutrition_bases[0],
        kind=BasisKind.PER_SERVING,
        serving_size=ServingSize(Decimal("30"), AmountUnit.GRAM),
    )
    food_input = CustomFoodInput(name="Oats", nutrition_bases=(serving_basis,))

    with test_session_factory() as session:
        repository = SqlAlchemyFoodRepository(session)
        food = repository.save_custom_food(Food.create_custom(app_config.default_user_id, food_input))
        basis_row = session.scalar(select(FoodNutritionBasisRow))
        loaded_food = repository.get_custom_food(food.id, app_config.default_user_id)

    assert basis_row is not None
    assert basis_row.basis_quantity == 1_000_000
    assert basis_row.basis_unit == "serving"
    assert basis_row.serving_equivalent_quantity == 30_000_000
    assert loaded_food is not None
    assert loaded_food.nutrition_bases[0].serving_size == ServingSize(Decimal("30"), AmountUnit.GRAM)
