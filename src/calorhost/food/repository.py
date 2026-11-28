"""Food repository interface and SQLAlchemy implementation."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .domain import (
    AmountUnit,
    BasisKind,
    Food,
    FoodKind,
    NutrientAmount,
    NutrientCode,
    NutritionBasis,
    ServingSize,
)
from .orm_models import FoodNutrientValueRow, FoodNutritionBasisRow, FoodRow

_SCALE = Decimal(1_000_000)


def _to_scaled_integer(value: Decimal) -> int:
    """Convert a decimal to the database's millionths representation."""
    return int((value * _SCALE).to_integral_value(rounding=ROUND_HALF_UP))


def _from_scaled_integer(value: int) -> Decimal:
    """Convert an integer millionths value to a decimal."""
    return Decimal(value) / _SCALE


class FoodRepository(Protocol):
    """Persistence operations used by custom-food services."""

    def list_custom_foods(self, owner_user_id: str) -> list[Food]:
        """List custom foods belonging to one user."""
        ...

    def get_custom_food(self, food_id: str, owner_user_id: str) -> Food | None:
        """Get one custom food belonging to one user."""
        ...

    def save_custom_food(self, food: Food) -> Food:
        """Create or replace a custom food and its nutrition data."""
        ...


class SqlAlchemyFoodRepository(FoodRepository):
    """SQLAlchemy-backed food persistence."""

    def __init__(self, session: Session) -> None:
        """Create a repository using the supplied session."""
        self._session = session

    def list_custom_foods(self, owner_user_id: str) -> list[Food]:
        """List a user's custom foods by name."""
        statement = (
            select(FoodRow)
            .where(FoodRow.owner_user_id == owner_user_id, FoodRow.kind == FoodKind.CUSTOM.value)
            .options(selectinload(FoodRow.nutrition_bases).selectinload(FoodNutritionBasisRow.nutrient_values))
            .order_by(FoodRow.name, FoodRow.id)
        )
        return [self._to_domain(row) for row in self._session.scalars(statement)]

    def get_custom_food(self, food_id: str, owner_user_id: str) -> Food | None:
        """Get a custom food by ID and owner."""
        statement = (
            select(FoodRow)
            .where(
                FoodRow.id == food_id,
                FoodRow.owner_user_id == owner_user_id,
                FoodRow.kind == FoodKind.CUSTOM.value,
            )
            .options(selectinload(FoodRow.nutrition_bases).selectinload(FoodNutritionBasisRow.nutrient_values))
        )
        row = self._session.scalar(statement)
        if row is None:
            return None
        return self._to_domain(row)

    def save_custom_food(self, food: Food) -> Food:
        """Persist a custom food and replace its nutrition bases atomically."""
        row = self._session.get(FoodRow, food.id)
        if row is None:
            row = FoodRow(
                id=food.id,
                owner_user_id=food.owner_user_id,
                kind=food.kind.value,
                source_name=food.source_name,
            )
            self._session.add(row)
        elif row.kind != FoodKind.CUSTOM.value or row.owner_user_id != food.owner_user_id:
            raise ValueError("Only the owning user can update a custom food.")

        try:
            row.name = food.name
            row.kind = food.kind.value
            row.source_name = food.source_name
            row.nutrition_bases.clear()
            self._session.flush()
            row.nutrition_bases = [self._to_row(basis) for basis in food.nutrition_bases]
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return food

    @staticmethod
    def _to_domain(row: FoodRow) -> Food:
        """Convert a database row into a food domain object."""
        nutrition_bases = tuple(
            NutritionBasis(
                kind=BasisKind(basis.basis_kind),
                values=tuple(
                    NutrientAmount(
                        nutrient=NutrientCode(value.nutrient_code),
                        value=_from_scaled_integer(value.value),
                    )
                    for value in basis.nutrient_values
                ),
                serving_size=(
                    ServingSize(
                        quantity=_from_scaled_integer(basis.serving_equivalent_quantity),
                        unit=AmountUnit(basis.serving_equivalent_unit),
                    )
                    if basis.serving_equivalent_quantity is not None and basis.serving_equivalent_unit is not None
                    else None
                ),
            )
            for basis in row.nutrition_bases
        )
        return Food(
            id=row.id,
            owner_user_id=row.owner_user_id,
            name=row.name,
            kind=FoodKind(row.kind),
            source_name=row.source_name,
            nutrition_bases=nutrition_bases,
        )

    @staticmethod
    def _to_row(basis: NutritionBasis) -> FoodNutritionBasisRow:
        """Convert a domain nutrition basis to a database row."""
        if basis.kind is BasisKind.PER_100G:
            basis_quantity = Decimal(100)
            basis_unit = AmountUnit.GRAM.value
        else:
            basis_quantity = Decimal(1)
            basis_unit = AmountUnit.SERVING.value

        return FoodNutritionBasisRow(
            id=str(uuid4()),
            basis_kind=basis.kind.value,
            basis_quantity=_to_scaled_integer(basis_quantity),
            basis_unit=basis_unit,
            serving_equivalent_quantity=(
                _to_scaled_integer(basis.serving_size.quantity) if basis.serving_size is not None else None
            ),
            serving_equivalent_unit=(basis.serving_size.unit.value if basis.serving_size is not None else None),
            nutrient_values=[
                FoodNutrientValueRow(nutrient_code=value.nutrient.value, value=_to_scaled_integer(value.value))
                for value in basis.values
            ],
        )
