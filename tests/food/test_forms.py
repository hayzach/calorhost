"""Tests for custom-food form parsing."""

from decimal import Decimal

import pytest

from calorhost.app_config import AppConfig
from calorhost.food.domain import BasisKind, FoodValidationError, NutrientCode
from calorhost.food.forms import parse_custom_food_form

app_config = AppConfig()


def test_form_parser_converts_energy_to_kcal() -> None:
    """Energy submitted in kilojoules is normalized to kcal."""
    food_input = parse_custom_food_form(
        {
            "name": "Rice",
            "per_100g_energy": "418.4",
            "per_100g_energy_unit": "kJ",
            "per_100g_protein": "0",
            "per_100g_fat": "0",
            "per_100g_carbohydrates": "0",
        }
    )

    assert food_input.nutrition_bases[0].kind is BasisKind.PER_100G
    assert food_input.nutrition_bases[0].values[0].nutrient is NutrientCode.ENERGY
    assert food_input.nutrition_bases[0].values[0].value == Decimal("100")
    assert (
        next(value for value in food_input.nutrition_bases[0].values if value.nutrient is NutrientCode.PROTEIN).value
        == 0
    )


@pytest.mark.parametrize("value", ["abc", "-1", "NaN", "Infinity"])
def test_form_parser_rejects_invalid_nutrient_values(value: str) -> None:
    """Malformed, negative, or non-finite nutrient values are rejected."""
    with pytest.raises(FoodValidationError) as error:
        parse_custom_food_form(
            {
                "name": "Rice",
                "per_100g_energy": value,
                "per_100g_protein": "1",
                "per_100g_fat": "1",
                "per_100g_carbohydrates": "1",
            }
        )

    assert "per_100g_energy" in error.value.field_errors


def test_form_parser_records_serving_size_without_assuming_other_units() -> None:
    """The form parser retains an optional serving size and unit."""
    food_input = parse_custom_food_form(
        {
            "name": "Milk",
            "serving_size": "250",
            "serving_unit": "ml",
            "per_serving_energy": "100",
            "per_serving_protein": "3",
            "per_serving_fat": "2",
            "per_serving_carbohydrates": "4",
        }
    )

    assert food_input.nutrition_bases[0].serving_size is not None
    assert food_input.nutrition_bases[0].serving_size.unit.value == "ml"
    assert food_input.nutrition_bases[0].serving_size.quantity == Decimal("250")


def test_form_parser_rejects_invalid_serving_size() -> None:
    """Serving conversions require a positive size in grams or millilitres."""
    with pytest.raises(FoodValidationError) as error:
        parse_custom_food_form(
            {
                "name": "Milk",
                "serving_size": "0",
                "serving_unit": "ml",
                "per_serving_energy": "100",
                "per_serving_protein": "3",
                "per_serving_fat": "2",
                "per_serving_carbohydrates": "4",
            }
        )

    assert error.value.field_errors["serving_size"] == "Serving size must be greater than zero."


def test_form_parser_rejects_oversized_energy_before_unit_conversion() -> None:
    """Very large kilojoule values return validation errors instead of overflowing Decimal arithmetic."""
    with pytest.raises(FoodValidationError) as error:
        parse_custom_food_form(
            {
                "name": "Rice",
                "per_100g_energy": "1e100",
                "per_100g_energy_unit": "kJ",
                "per_100g_protein": "1",
                "per_100g_fat": "1",
                "per_100g_carbohydrates": "1",
            }
        )

    maximum_energy_kj = app_config.max_food_value * Decimal("4.184")
    assert error.value.field_errors["per_100g_energy"] == f"Enter a value no greater than {maximum_energy_kj:,f}."
