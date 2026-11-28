"""Tests for food-domain validation."""

from dataclasses import replace
from decimal import Decimal

import pytest

from calorhost.app_config import AppConfig
from calorhost.food.domain import (
    AmountUnit,
    BasisKind,
    CustomFoodInput,
    Food,
    FoodValidationError,
    NutrientAmount,
    NutrientCode,
    NutritionBasis,
    ServingSize,
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


def test_custom_food_rejects_values_that_exceed_storage_range(custom_food_input: CustomFoodInput) -> None:
    """Nutrient values beyond the scaled-integer range are rejected before persistence."""
    basis = custom_food_input.nutrition_bases[0]
    oversized_energy = replace(basis.values[0], value=app_config.max_food_value + Decimal("0.000001"))
    food_input = replace(
        custom_food_input,
        nutrition_bases=(replace(basis, values=(oversized_energy, *basis.values[1:])),),
    )

    with pytest.raises(FoodValidationError) as error:
        Food.create_custom(app_config.default_user_id, food_input)

    assert error.value.field_errors[NutrientCode.ENERGY.value] == (
        f"Enter a value no greater than {app_config.max_food_value:,f}."
    )


def test_custom_food_rejects_oversized_serving_size(custom_food_input: CustomFoodInput) -> None:
    """Serving sizes beyond the scaled-integer range are rejected."""
    basis = replace(
        custom_food_input.nutrition_bases[0],
        serving_size=ServingSize(app_config.max_food_value + Decimal("0.000001"), AmountUnit.GRAM),
    )

    with pytest.raises(FoodValidationError) as error:
        Food.create_custom(app_config.default_user_id, replace(custom_food_input, nutrition_bases=(basis,)))

    assert error.value.field_errors["serving_size"] == f"Enter a value no greater than {app_config.max_food_value:,f}."
