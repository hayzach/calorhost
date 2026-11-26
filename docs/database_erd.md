# Calorie Tracker Database ERD

This is an SQLite-oriented initial design for the single-user MVP

## Design notes

- Store application-generated UUIDs as canonical text, dates and timestamps as
  ISO-8601 text, booleans as `0`/`1` integers, and decimal quantities as integer
  millionths. For example, store `150.25 g` as `150250000`. Convert scaled
  values to and from `Decimal` in the application; avoid SQLite `REAL` for
  nutrition and measurements.
- Enable SQLite foreign keys (`PRAGMA foreign_keys = ON`) on every connection.
  Add `CHECK` constraints for booleans, positive quantities, allowed enum-like
  values, and recipe requirements because SQLite does not strictly enforce
  declared types.
- Store timestamps in UTC using one ISO-8601 format. Store
  `MEAL_ENTRIES.log_date` as the user's selected calendar date (`YYYY-MM-DD`),
  not a timestamp.
- Use the same nutrient model for all nutrients. A missing
  `FOOD_NUTRIENT_VALUES` row means the value is unknown; a row with value `0`
  means zero is known. Require energy, protein, fat, and carbohydrates together
  on at least one basis for every usable food. Zero is valid for all four.
- Accept energy in kcal or kJ and normalize it to the canonical unit, kcal.
  Missing values for all other nutrients contribute zero to calculations, while
  remaining distinct from known zero in storage.
- Enforce required nutrient completeness in application validation because it
  spans nutrition bases and nutrient-value rows.
- Store a per-100-g basis as `basis_quantity = 100`, `basis_unit = g`, and a
  per-serving basis as `basis_quantity = 1`, `basis_unit = serving`. When known,
  `serving_equivalent_quantity` and `serving_equivalent_unit` record the serving's
  weight or volume for conversion to g or ml.
- Use the basis matching the logged amount unit when available. If a nutrient is
  absent from that basis, use another basis only when a known conversion applies.
  The required four nutrients must be calculable for the selected amount unit.
- `FOOD_NUTRITION_BASES` and `FOOD_NUTRIENT_VALUES` hold imported or user-entered
  nutrition. Calculate recipe nutrition from ingredients rather than storing
  aggregate values in these tables.
- For text or barcode OFF searches, save or update the local food only when the
  user commits a meal entry. Update from the latest OFF response and snapshot
  that same data in one transaction. Canceling the flow leaves local data
  unchanged.
- Snapshot meal-entry nutrient totals when food is logged so later changes to a
  food or recipe do not alter historical entries. Editing an amount uses its
  existing snapshot; selecting a different food uses current data.
- Aggregate dashboard meal and daily totals from `MEAL_ENTRY_NUTRIENTS` by user,
  date, meal, and nutrient; no separate totals are needed.
- Index `FOODS.name` and `FOODS.brand`, and add a SQLite partial unique index on
  `(source_name, source_product_id)` where `source_product_id IS NOT NULL`.
- Require at least one of `servings_count` and `finished_weight_g` in each
  recipe, and require each provided value to be positive. Either value supports
  its corresponding nutrition basis; both support per-serving and per-100-g
  calculations. Finished weight is the prepared recipe's weight, not the sum of
  raw ingredient weights. Calculate recipe nutrition dynamically from current
  ingredient data, require at least one ingredient, and snapshot totals in
  `MEAL_ENTRY_NUTRIENTS` when logged. Allow fractional serving counts. Prevent
  direct and indirect recipe cycles.
- Do not archive foods. Block deleting a food or recipe while a recipe uses it.
  When deleting an unreferenced food, set historical `MEAL_ENTRIES.food_id` to
  NULL and retain its name and nutrient snapshots. Deleting a meal entry does not
  delete its food.
- For the MVP, meal and recipe-ingredient amounts use g, ml, or a serving only
  when the food has a defined conversion. Household portions need food-specific
  conversions; grams and millilitres are not interchangeable.

## Entity relationship diagram

```mermaid
erDiagram
    USERS {
        text id PK "UUID"
        text created_at "ISO-8601 UTC"
        text timezone "browser-detected; user-editable"
        text weight_display_unit "kg or lb; body-weight input and display only"
    }

    FOODS {
        text id PK "UUID"
        text owner_user_id FK
        text created_at "ISO-8601 UTC"
        text updated_at "ISO-8601 UTC"
        text source_updated_at "nullable; ISO-8601 UTC"
        text kind "openfoodfacts, custom, recipe"
        text name
        text brand "nullable"
        text barcode "nullable"
        text source_name "openfoodfacts or user"
        text source_product_id "nullable; OFF product code"
    }

    NUTRIENTS {
        text code PK
        text name
        text category "energy, macro, micro, other"
        text canonical_unit "kcal, g, mg, ug, etc"
        integer display_order
    }

    FOOD_NUTRITION_BASES {
        text id PK "UUID"
        text food_id FK
        text basis_kind "mass, volume, serving"
        integer basis_quantity "scaled by 1,000,000"
        text basis_unit "g, ml, serving"
        integer serving_equivalent_quantity "nullable; scaled by 1,000,000"
        text serving_equivalent_unit "nullable; g or ml"
        text source_basis_label "nullable; original label text"
        integer is_primary "boolean: 0 or 1"
    }

    FOOD_NUTRIENT_VALUES {
        text nutrition_basis_id PK "composite PK; FK to FOOD_NUTRITION_BASES"
        text nutrient_code PK "composite PK; FK to NUTRIENTS"
        integer value "millionths of canonical unit"
    }

    RECIPES {
        text food_id PK "UUID FK to FOODS; recipe subtype"
        integer servings_count "nullable; scaled; positive; fractional allowed"
        integer finished_weight_g "nullable; scaled; final prepared recipe weight"
        text updated_at "ISO-8601 UTC"
    }

    RECIPE_INGREDIENTS {
        text id PK "UUID"
        text recipe_food_id FK
        text ingredient_food_id FK "may reference another recipe"
        integer amount "scaled by 1,000,000"
        text amount_unit "MVP: g, ml, or convertible serving"
        integer position
    }

    MEAL_ENTRIES {
        text id PK "UUID"
        text user_id FK
        text food_id FK "nullable; set NULL if food is removed"
        text food_name_snapshot "name at time of logging"
        text log_date "YYYY-MM-DD; user-selected, past or future"
        text meal_type "breakfast, lunch, dinner, snack"
        integer amount "scaled by 1,000,000"
        text amount_unit "MVP: g, ml, or convertible serving"
        text created_at "ISO-8601 UTC"
        text updated_at "ISO-8601 UTC"
    }

    MEAL_ENTRY_NUTRIENTS {
        text meal_entry_id PK "composite PK; FK to MEAL_ENTRIES"
        text nutrient_code PK "composite PK; FK to NUTRIENTS"
        integer total_value "millionths; snapshot total for logged amount"
        text unit_snapshot "unit used at log time"
    }

    WEIGHT_ENTRIES {
        text id PK "UUID"
        text user_id FK
        text created_at "ISO-8601 UTC"
        text recorded_at "ISO-8601 UTC"
        integer weight_kg "millionths of kg; always stored in kg"
    }

    USERS o|--o{ FOODS : owns_custom_foods_and_recipes

    FOODS ||--o{ FOOD_NUTRITION_BASES : has_bases
    FOOD_NUTRITION_BASES ||--o{ FOOD_NUTRIENT_VALUES : records
    NUTRIENTS ||--o{ FOOD_NUTRIENT_VALUES : defines

    FOODS ||--o| RECIPES : recipe_details
    RECIPES ||--o{ RECIPE_INGREDIENTS : contains
    FOODS ||--o{ RECIPE_INGREDIENTS : used_as_ingredient

    USERS ||--o{ MEAL_ENTRIES : logs
    FOODS o|--o{ MEAL_ENTRIES : logged_food
    MEAL_ENTRIES ||--o{ MEAL_ENTRY_NUTRIENTS : snapshots
    NUTRIENTS ||--o{ MEAL_ENTRY_NUTRIENTS : defines

    USERS ||--o{ WEIGHT_ENTRIES : records
```
