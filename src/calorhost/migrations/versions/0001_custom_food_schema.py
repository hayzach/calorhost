"""Create food tables and seed the single default user and nutrient catalog."""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0001_custom_food_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create the tables needed to store custom foods."""
    op.create_table(
        "users",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("weight_display_unit", sa.Text(), nullable=False),
        sa.CheckConstraint("weight_display_unit IN ('kg', 'lbs')", name="ck_users_weight_display_unit"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_table(
        "nutrients",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("canonical_unit", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_nutrients"),
    )
    op.create_table(
        "foods",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("owner_user_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("barcode", sa.Text(), nullable=True),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("source_product_id", sa.Text(), nullable=True),
        sa.CheckConstraint("kind IN ('openfoodfacts', 'custom', 'recipe')", name="ck_foods_kind"),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="fk_foods_owner_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_foods"),
    )
    op.create_index("ix_foods_name", "foods", ["name"])
    op.create_index(
        "uq_foods_source_product",
        "foods",
        ["source_name", "source_product_id"],
        unique=True,
        sqlite_where=sa.text("source_product_id IS NOT NULL"),
    )
    op.create_table(
        "food_nutrition_bases",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("food_id", sa.Text(), nullable=False),
        sa.Column("basis_kind", sa.Text(), nullable=False),
        sa.Column("basis_quantity", sa.Integer(), nullable=False),
        sa.Column("basis_unit", sa.Text(), nullable=False),
        sa.Column("serving_equivalent_quantity", sa.Integer(), nullable=True),
        sa.Column("serving_equivalent_unit", sa.Text(), nullable=True),
        sa.CheckConstraint("basis_kind IN ('mass', 'volume', 'serving')", name="ck_food_nutrition_bases_basis_kind"),
        sa.CheckConstraint("basis_quantity > 0", name="ck_food_nutrition_bases_basis_quantity_positive"),
        sa.CheckConstraint("basis_unit IN ('g', 'ml', 'serving')", name="ck_food_nutrition_bases_basis_unit"),
        sa.CheckConstraint(
            "(serving_equivalent_quantity IS NULL AND serving_equivalent_unit IS NULL) OR "
            "(serving_equivalent_quantity > 0 AND serving_equivalent_unit IN ('g', 'ml'))",
            name="ck_food_nutrition_bases_serving_equivalent",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"], name="fk_food_nutrition_bases_food_id_foods", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_food_nutrition_bases"),
        sa.UniqueConstraint("food_id", "basis_kind", name="uq_food_nutrition_bases_food_kind"),
    )
    op.create_table(
        "food_nutrient_values",
        sa.Column("nutrition_basis_id", sa.Text(), nullable=False),
        sa.Column("nutrient_code", sa.Text(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.CheckConstraint("value >= 0", name="ck_food_nutrient_values_value_nonnegative"),
        sa.ForeignKeyConstraint(
            ["nutrient_code"], ["nutrients.code"], name="fk_food_nutrient_values_nutrient_code_nutrients"
        ),
        sa.ForeignKeyConstraint(
            ["nutrition_basis_id"],
            ["food_nutrition_bases.id"],
            name="fk_food_nutrient_values_nutrition_basis_id_food_nutrition_bases",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("nutrition_basis_id", "nutrient_code", name="pk_food_nutrient_values"),
    )

    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", sa.Text()),
            sa.column("created_at", sa.Text()),
            sa.column("timezone", sa.Text()),
            sa.column("weight_display_unit", sa.Text()),
        ),
        [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "created_at": created_at,
                "timezone": "UTC",
                "weight_display_unit": "kg",
            }
        ],
        multiinsert=False,
    )

    nutrient_table = sa.table(
        "nutrients",
        sa.column("code", sa.Text()),
        sa.column("name", sa.Text()),
        sa.column("canonical_unit", sa.Text()),
        sa.column("display_order", sa.Integer()),
    )
    op.bulk_insert(
        nutrient_table,
        [
            {"code": "energy", "name": "Energy", "canonical_unit": "kcal", "display_order": 1},
            {"code": "protein", "name": "Protein", "canonical_unit": "g", "display_order": 2},
            {
                "code": "carbohydrates",
                "name": "Carbohydrates",
                "canonical_unit": "g",
                "display_order": 3,
            },
            {"code": "fat", "name": "Fat", "canonical_unit": "g", "display_order": 4},
            {"code": "fiber", "name": "Fiber", "canonical_unit": "g", "display_order": 5},
            {"code": "sugars", "name": "Sugars", "canonical_unit": "g", "display_order": 6},
            {
                "code": "saturated_fat",
                "name": "Saturated fat",
                "canonical_unit": "g",
                "display_order": 7,
            },
            {
                "code": "trans_fat",
                "name": "Trans fat",
                "canonical_unit": "g",
                "display_order": 8,
            },
            {"code": "sodium", "name": "Sodium", "canonical_unit": "mg", "display_order": 9},
            {
                "code": "potassium",
                "name": "Potassium",
                "canonical_unit": "mg",
                "display_order": 10,
            },
            {"code": "calcium", "name": "Calcium", "canonical_unit": "mg", "display_order": 11},
            {"code": "iron", "name": "Iron", "canonical_unit": "mg", "display_order": 12},
            {
                "code": "vitamin_a",
                "name": "Vitamin A",
                "canonical_unit": "ug",
                "display_order": 13,
            },
            {
                "code": "vitamin_c",
                "name": "Vitamin C",
                "canonical_unit": "mg",
                "display_order": 14,
            },
            {
                "code": "vitamin_d",
                "name": "Vitamin D",
                "canonical_unit": "ug",
                "display_order": 15,
            },
        ],
        multiinsert=False,
    )


def downgrade() -> None:
    """Drop the custom-food schema."""
    op.drop_table("food_nutrient_values")
    op.drop_table("food_nutrition_bases")
    op.drop_index("uq_foods_source_product", table_name="foods")
    op.drop_index("ix_foods_name", table_name="foods")
    op.drop_table("foods")
    op.drop_table("nutrients")
    op.drop_table("users")
