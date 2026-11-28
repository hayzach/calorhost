"""Tests for food-domain validation."""

from dataclasses import replace
from decimal import Decimal

import pytest

from calorhost.app_config import AppConfig
from calorhost.food.domain import (
    BasisKind,
    CustomFoodInput,
    Food,
    FoodValidationError,
    NutrientAmount,
    NutrientCode,
    NutritionBasis,
)

app_config = AppConfig()


def test_custom_food_accepts_zero_and_keeps_missing_values_unknown(custom_food_input: CustomFoodInput) -> None:
    """A known zero remains present while an unentered nutrient stays missing."""
    food = Food.create_custom(app_config.default_user_id, replace(custom_food_input, name="  Rolled oats  "))

    known_values = {item.nutrient: item.value for item in food.nutrition_bases[0].values}

    assert food.name == "Rolled oats"
    assert known_values[NutrientCode.ENERGY] == Decimal("0")
    assert NutrientCode.FIBER not in known_values


def test_every_nutrition_basis_requires_all_required_nutrients(custom_food_input: CustomFoodInput) -> None:
    """Each basis must include energy, protein, fat, and carbohydrates."""
    incomplete_serving_basis = NutritionBasis(
        BasisKind.PER_SERVING,
        (
            NutrientAmount(NutrientCode.FAT, Decimal("1")),
            NutrientAmount(NutrientCode.CARBOHYDRATES, Decimal("3")),
        ),
    )
    food_input = replace(
        custom_food_input,
        nutrition_bases=(*custom_food_input.nutrition_bases, incomplete_serving_basis),
    )

    with pytest.raises(FoodValidationError) as error:
        Food.create_custom(app_config.default_user_id, food_input)

    assert error.value.field_errors["nutrition"] == (
        "Each nutrition basis must include energy, protein, fat, and carbohydrates."
    )


def test_custom_food_requires_a_name(custom_food_input: CustomFoodInput) -> None:
    """Whitespace-only names are rejected."""
    with pytest.raises(FoodValidationError) as error:
        Food.create_custom(app_config.default_user_id, replace(custom_food_input, name="  "))

    assert error.value.field_errors["name"] == "Enter a food name."
