"""SQLAlchemy mappings for users and food nutrition."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class UserRow(Base):
    """Database row for an application user."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("weight_display_unit IN ('kg', 'lbs')", name="weight_display_unit"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="UTC")
    weight_display_unit: Mapped[str] = mapped_column(Text, nullable=False, default="kg")


class NutrientRow(Base):
    """Database row for a nutrient definition."""

    __tablename__ = "nutrients"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_unit: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class FoodRow(Base):
    """Database row for a food catalog entry."""

    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("kind IN ('openfoodfacts', 'custom', 'recipe')", name="kind"),
        Index("ix_foods_name", "name"),
        Index(
            "uq_foods_source_product",
            "source_name",
            "source_product_id",
            unique=True,
            sqlite_where=text("source_product_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso, onupdate=utc_now_iso)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(Text)
    barcode: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_product_id: Mapped[str | None] = mapped_column(Text)

    nutrition_bases: Mapped[list[FoodNutritionBasisRow]] = relationship(
        back_populates="food",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FoodNutritionBasisRow(Base):
    """Database row for a food's nutrition basis."""

    __tablename__ = "food_nutrition_bases"
    __table_args__ = (
        CheckConstraint("basis_kind IN ('mass', 'volume', 'serving')", name="basis_kind"),
        CheckConstraint("basis_quantity > 0", name="basis_quantity_positive"),
        CheckConstraint("basis_unit IN ('g', 'ml', 'serving')", name="basis_unit"),
        CheckConstraint(
            "(serving_equivalent_quantity IS NULL AND serving_equivalent_unit IS NULL) OR "
            "(serving_equivalent_quantity > 0 AND serving_equivalent_unit IN ('g', 'ml'))",
            name="serving_equivalent",
        ),
        UniqueConstraint("food_id", "basis_kind", name="uq_food_nutrition_bases_food_kind"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    food_id: Mapped[str] = mapped_column(Text, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    basis_kind: Mapped[str] = mapped_column(Text, nullable=False)
    basis_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    basis_unit: Mapped[str] = mapped_column(Text, nullable=False)
    serving_equivalent_quantity: Mapped[int | None] = mapped_column(Integer)
    serving_equivalent_unit: Mapped[str | None] = mapped_column(Text)

    food: Mapped[FoodRow] = relationship(back_populates="nutrition_bases")
    nutrient_values: Mapped[list[FoodNutrientValueRow]] = relationship(
        back_populates="nutrition_basis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FoodNutrientValueRow(Base):
    """Database row for a known nutrient value on one basis."""

    __tablename__ = "food_nutrient_values"
    __table_args__ = (CheckConstraint("value >= 0", name="value_nonnegative"),)

    nutrition_basis_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("food_nutrition_bases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    nutrient_code: Mapped[str] = mapped_column(Text, ForeignKey("nutrients.code"), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    nutrition_basis: Mapped[FoodNutritionBasisRow] = relationship(back_populates="nutrient_values")
