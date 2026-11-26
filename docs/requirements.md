# Requirements

## MVP requirements

### Food catalog

- Search Open Food Facts (OFF) by text or camera-based barcode scan. Include
  locally saved foods in text results, without prioritizing them over OFF results
  in the MVP.
- Include only OFF search results with energy, protein, fat, and carbohydrates
  present together in at least one nutrition basis. Accept energy in kcal or kJ
  and store it as kcal. Zero is valid for all four values.
- Store each food's name, source, optional barcode, and nutrition values with
  their basis (e.g., per 100 g or per serving). Support conversions when the
  serving size is known.
- Prefer per-100-g values in search results. Show serving data too when
  available, or use it when no per-100-g basis exists. Let users choose the
  amount unit for each meal entry.
- For text and barcode search, open the selected OFF product in the meal-entry
  flow. Save it locally only when the meal is added. At that point, create or
  update the local food with the latest OFF data. Keep the food if its meal entry
  is later deleted.
- Keep saved foods available when OFF is unavailable.
- Allow users to create and edit custom foods independently of meal logging.
  Custom foods must have energy, protein, fat, and carbohydrates.
- Distinguish missing nutrition data from a measured value of zero. Missing
  values for other nutrients contribute zero to calculations and display as not
  provided in food details.
- The MVP is desktop-focused, but camera scanning must work on desktop, phones,
  and tablets. Barcode scanning searches OFF only; show a retry option if it
  fails. Do not provide manual barcode entry. Do not store or upload camera
  images.

### Food logging and meals

- Let users choose an amount and unit for each food logged under breakfast,
  lunch, dinner, or snacks on any chosen date, including past or future dates.
- For the MVP, support grams, millilitres, and a food's serving unit only when
  the nutrition basis can be converted to that unit. Do not assume grams and
  millilitres are interchangeable.
- Allow users to edit and delete logged items.
- Calculate logged nutrition from the amount. For example, 150 g of a food with
  200 kcal per 100 g should log as 300 kcal.
- Save the nutrition values used at logging time so later food edits do not
  change past meals. Editing an amount uses its existing snapshot; selecting a
  different food uses that food's current data.

### Daily view and totals

- Show calories, protein, carbohydrates, fat, and fiber for each meal and the
  full day on the dashboard. Display energy in kcal.
- Let users expand the view to see sugars, saturated fat, trans fat, sodium,
  potassium, calcium, iron, and vitamins A, C, and D.
- Recalculate totals when a logged item is added, edited, or deleted.
- Allow users to view past and future dates.

### User profile

- Let users record weight with a date and time.
- Store weight in kilograms. Let users enter and view pounds using a saved
  preference that applies only to weight entries. Allow a per-entry unit override.
- Preserve earlier measurements when a new weight is recorded.
- Allow users to edit and delete weight entries.
- Detect the user's timezone from the browser and let them change it. Use it for
  weight-entry times and the dashboard's default date.
- Support a single user initially.

### Recipes

- Let users create, edit, and delete recipes from other foods. Require at least
  one ingredient before saving a recipe.
- Use grams, millilitres, or a serving as ingredient units only when the food
  has a defined conversion.
- Store a recipe's positive serving count, including fractional counts, and
  finished weight in grams independently. At least one is required; when both
  are known, support nutrition per serving and per 100 g.
- Treat finished weight as the prepared recipe's weight, not the sum of raw
  ingredient weights.
- Calculate current recipe nutrition from its ingredients, amounts, and current
  nutrition data. Ingredient or food-data changes affect the calculation.
- Snapshot calculated nutrition when a recipe is logged so later changes do not
  alter past logs.
- A recipe can contain another recipe. Prevent direct and indirect recipe cycles.
- Prevent deleting a food or recipe while a recipe uses it. Do not archive foods;
  when an unreferenced food is deleted, clear its meal-entry reference and keep
  the meal's name and nutrient snapshots.

## Post-MVP

- Show weight history or trends over time.
- Let users set a starting weight and date, and a goal weight.
- Let users set a daily target for kcal, protein, fats, carbohydrates and fiber.
  - Update dashboard to show the amount of kcal, protein, fats, carbohydrates
    and fiber per day in relation to their target
- Prioritize matching foods saved locally over upstream search results.
- Support named household portions (e.g., a slice or cup) with food-specific
  conversions to grams or millilitres in a `FOOD_PORTIONS` table. Do not assume
  universal conversions.
- Add authentication and support multiple users.
