"""Parsing and rendering helpers for custom-food forms."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from ..app_config import AppConfig
from .domain import (
    NUTRIENT_DEFINITIONS,
    AmountUnit,
    BasisKind,
    CustomFoodInput,
    Food,
    FoodValidationError,
    NutrientAmount,
    NutrientCode,
    NutritionBasis,
    ServingSize,
    value_limit_error_message,
)

app_config = AppConfig()

_ENERGY_CONVERSION = Decimal("4.184")
_ENERGY_UNITS = {"kcal", "kJ"}


def parse_custom_food_form(values: Mapping[str, str]) -> CustomFoodInput:
    """Parse form fields and normalize submitted energy to kcal."""
    errors: dict[str, str] = {}

    name = values.get("name", "").strip()
    if not name:
        errors["name"] = "Enter a food name."

    serving_size, serving_size_errors = _parse_serving_size(values)
    errors.update(serving_size_errors)

    nutrition_bases: list[NutritionBasis] = []
    for basis_kind, prefix in (
        (BasisKind.PER_100G, "per_100g"),
        (BasisKind.PER_SERVING, "per_serving"),
    ):
        nutrient_values: list[NutrientAmount] = []
        for nutrient_definition in NUTRIENT_DEFINITIONS:
            field_name = f"{prefix}_{nutrient_definition.code.value}"
            raw_value = values.get(field_name, "").strip()
            if not raw_value:
                continue

            try:
                value = Decimal(raw_value)
            except InvalidOperation:
                errors[field_name] = "Enter a valid number."
                continue

            if not value.is_finite() or value < 0:
                errors[field_name] = "Enter a number that is zero or greater."
                continue

            if nutrient_definition.code is NutrientCode.ENERGY:
                energy_unit = values.get(f"{prefix}_energy_unit", "kcal")
                if energy_unit not in _ENERGY_UNITS:
                    errors[f"{prefix}_energy_unit"] = "Choose kcal or kJ."
                    continue
                maximum_value = app_config.max_food_value * (_ENERGY_CONVERSION if energy_unit == "kJ" else 1)
                if value > maximum_value:
                    errors[field_name] = value_limit_error_message(maximum_value)
                    continue
                if energy_unit == "kJ":
                    value /= _ENERGY_CONVERSION
            elif value > app_config.max_food_value:
                errors[field_name] = value_limit_error_message(app_config.max_food_value)
                continue

            nutrient_values.append(NutrientAmount(nutrient_definition.code, value))

        if nutrient_values:
            nutrition_bases.append(NutritionBasis(basis_kind, tuple(nutrient_values), serving_size))

    if errors:
        raise FoodValidationError(errors)
    return CustomFoodInput(name=name, nutrition_bases=tuple(nutrition_bases))


def form_values_from_food(food: Food) -> dict[str, str]:
    """Create editable form values from a saved custom food."""
    values: dict[str, str] = {"name": food.name, "serving_unit": AmountUnit.GRAM.value}
    for prefix in ("per_100g", "per_serving"):
        values[f"{prefix}_energy_unit"] = "kcal"

    for basis in food.nutrition_bases:
        prefix = "per_100g" if basis.kind is BasisKind.PER_100G else "per_serving"
        for amount in basis.values:
            values[f"{prefix}_{amount.nutrient.value}"] = format(amount.value, "f")

        if basis.serving_size is not None:
            values["serving_size"] = format(basis.serving_size.quantity, "f")
            values["serving_unit"] = basis.serving_size.unit.value

    return values


def _parse_serving_size(values: Mapping[str, str]) -> tuple[ServingSize | None, dict[str, str]]:
    """Parse an optional serving size and its mass or volume unit."""
    errors: dict[str, str] = {}
    raw_size = values.get("serving_size", "").strip()
    raw_unit = values.get("serving_unit", AmountUnit.GRAM.value)
    if not raw_size:
        if "serving_unit" in values and raw_unit not in {AmountUnit.GRAM.value, AmountUnit.MILLILITRE.value}:
            errors["serving_unit"] = "Choose grams or millilitres."
        return None, errors

    try:
        quantity = Decimal(raw_size)
    except InvalidOperation:
        errors["serving_size"] = "Enter a valid serving size."
        return None, errors
    if not quantity.is_finite() or quantity <= 0:
        errors["serving_size"] = "Serving size must be greater than zero."
        return None, errors
    if quantity > app_config.max_food_value:
        errors["serving_size"] = value_limit_error_message(app_config.max_food_value)
        return None, errors
    if raw_unit not in {AmountUnit.GRAM.value, AmountUnit.MILLILITRE.value}:
        errors["serving_unit"] = "Choose grams or millilitres."
        return None, errors
    return ServingSize(quantity=quantity, unit=AmountUnit(raw_unit)), errors
