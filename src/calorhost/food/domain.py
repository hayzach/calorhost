"""Food-domain types and nutrition validation."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4

from ..app_config import AppConfig

app_config = AppConfig()


def value_limit_error_message(maximum: Decimal) -> str:
    """Describe the maximum value supported by food storage."""
    return f"Enter a value no greater than {maximum:,f}."


class FoodKind(StrEnum):
    """Supported food catalog kinds."""

    OPENFOODFACTS = "openfoodfacts"
    CUSTOM = "custom"
    RECIPE = "recipe"


class BasisKind(StrEnum):
    """Nutrition basis types supported for custom foods."""

    PER_100G = "mass"
    PER_SERVING = "serving"


class AmountUnit(StrEnum):
    """Units accepted for food amounts and serving sizes."""

    GRAM = "g"
    MILLILITRE = "ml"
    SERVING = "serving"


class NutrientCode(StrEnum):
    """Stable identifiers for supported nutrients."""

    ENERGY = "energy"
    PROTEIN = "protein"
    CARBOHYDRATES = "carbohydrates"
    FAT = "fat"
    FIBER = "fiber"
    SUGARS = "sugars"
    SATURATED_FAT = "saturated_fat"
    TRANS_FAT = "trans_fat"
    SODIUM = "sodium"
    POTASSIUM = "potassium"
    CALCIUM = "calcium"
    IRON = "iron"
    VITAMIN_A = "vitamin_a"
    VITAMIN_C = "vitamin_c"
    VITAMIN_D = "vitamin_d"


@dataclass(frozen=True)
class NutrientDefinition:
    """Display and canonical-unit metadata for a nutrient."""

    code: NutrientCode
    name: str
    canonical_unit: str
    display_order: int


NUTRIENT_DEFINITIONS = (
    NutrientDefinition(NutrientCode.ENERGY, "Energy", "kcal", 1),
    NutrientDefinition(NutrientCode.PROTEIN, "Protein", "g", 2),
    NutrientDefinition(NutrientCode.CARBOHYDRATES, "Carbohydrates", "g", 3),
    NutrientDefinition(NutrientCode.FAT, "Fat", "g", 4),
    NutrientDefinition(NutrientCode.FIBER, "Fiber", "g", 5),
    NutrientDefinition(NutrientCode.SUGARS, "Sugars", "g", 6),
    NutrientDefinition(NutrientCode.SATURATED_FAT, "Saturated fat", "g", 7),
    NutrientDefinition(NutrientCode.TRANS_FAT, "Trans fat", "g", 8),
    NutrientDefinition(NutrientCode.SODIUM, "Sodium", "mg", 9),
    NutrientDefinition(NutrientCode.POTASSIUM, "Potassium", "mg", 10),
    NutrientDefinition(NutrientCode.CALCIUM, "Calcium", "mg", 11),
    NutrientDefinition(NutrientCode.IRON, "Iron", "mg", 12),
    NutrientDefinition(NutrientCode.VITAMIN_A, "Vitamin A", "ug", 13),
    NutrientDefinition(NutrientCode.VITAMIN_C, "Vitamin C", "mg", 14),
    NutrientDefinition(NutrientCode.VITAMIN_D, "Vitamin D", "ug", 15),
)

REQUIRED_NUTRIENTS = frozenset(
    {NutrientCode.ENERGY, NutrientCode.PROTEIN, NutrientCode.FAT, NutrientCode.CARBOHYDRATES}
)


class FoodValidationError(ValueError):
    """Raised when food data does not satisfy domain requirements."""

    def __init__(self, field_errors: Mapping[str, str]) -> None:
        self.field_errors = dict(field_errors)
        super().__init__("The food details are incomplete or invalid.")


@dataclass(frozen=True)
class ServingSize:
    """A serving's known mass or volume."""

    quantity: Decimal
    unit: AmountUnit


@dataclass(frozen=True)
class NutrientAmount:
    """A known amount of one nutrient."""

    nutrient: NutrientCode
    value: Decimal


@dataclass(frozen=True)
class NutritionBasis:
    """Nutrients recorded on one food basis."""

    kind: BasisKind
    values: tuple[NutrientAmount, ...]
    serving_size: ServingSize | None = None


@dataclass(frozen=True)
class CustomFoodInput:
    """Validated-input shape used to create or edit a custom food."""

    name: str
    nutrition_bases: tuple[NutritionBasis, ...]


@dataclass(frozen=True)
class Food:
    """A food catalog entry and its nutrition data."""

    id: str
    owner_user_id: str
    name: str
    kind: FoodKind
    source_name: str
    nutrition_bases: tuple[NutritionBasis, ...]

    @classmethod
    def create_custom(
        cls,
        owner_user_id: str,
        food_input: CustomFoodInput,
        food_id: str | None = None,
    ) -> Food:
        """Validate and create a custom food domain object."""
        if food_id is None:
            food_id = str(uuid4())

        field_errors: dict[str, str] = {}
        name = food_input.name.strip()

        if not name:
            field_errors["name"] = "Enter a food name."
        if not food_input.nutrition_bases:
            field_errors["nutrition"] = "Enter nutrition for at least one basis."

        basis_kinds = [basis.kind for basis in food_input.nutrition_bases]
        if len(basis_kinds) != len(set(basis_kinds)):
            field_errors["nutrition"] = "Each nutrition basis can only be entered once."

        known_serving_sizes: set[ServingSize] = set()
        for basis in food_input.nutrition_bases:
            if basis.serving_size is not None:
                known_serving_sizes.add(basis.serving_size)

                if basis.serving_size.unit not in {AmountUnit.GRAM, AmountUnit.MILLILITRE}:
                    field_errors["serving_unit"] = "Serving size must use grams or millilitres."

                quantity = basis.serving_size.quantity
                if not quantity.is_finite() or quantity <= 0:
                    field_errors["serving_size"] = "Serving size must be greater than zero."
                elif quantity > app_config.max_food_value:
                    field_errors["serving_size"] = value_limit_error_message(app_config.max_food_value)

            nutrient_codes = [item.nutrient for item in basis.values]
            if len(nutrient_codes) != len(set(nutrient_codes)):
                field_errors["nutrition"] = "A nutrient can only be entered once per basis."
            if not REQUIRED_NUTRIENTS.issubset(set(nutrient_codes)):
                field_errors["nutrition"] = "Each nutrition basis must include energy, protein, fat, and carbohydrates."

            for item in basis.values:
                if not item.value.is_finite() or item.value < 0:
                    field_errors[item.nutrient.value] = "Nutrient values must be zero or greater."
                elif item.value > app_config.max_food_value:
                    field_errors[item.nutrient.value] = value_limit_error_message(app_config.max_food_value)

        # Each basis can include a serving size. If one says a serving is 30 g and another says
        # it's 40 g, converting a logged amount between servings and grams becomes ambiguous.
        # Therefore, enforce only one serving size
        if len(known_serving_sizes) > 1:
            field_errors["serving_size"] = "Use the same serving size for each nutrition basis."

        if field_errors:
            raise FoodValidationError(field_errors)

        return cls(
            id=food_id,
            owner_user_id=owner_user_id,
            name=name,
            kind=FoodKind.CUSTOM,
            source_name="user",
            nutrition_bases=food_input.nutrition_bases,
        )
