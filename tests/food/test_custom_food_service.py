"""Tests for custom-food application operations."""

import pytest

from calorhost.app_config import AppConfig
from calorhost.food.custom_food_service import CustomFoodNotFoundError, CustomFoodService
from calorhost.food.domain import CustomFoodInput, Food
from calorhost.food.repository import FoodRepository

app_config = AppConfig()


class InMemoryFoodRepository:
    """Small in-memory repository for service tests."""

    def __init__(self) -> None:
        """Create an empty food collection."""
        self.foods: dict[str, Food] = {}

    def list_custom_foods(self, owner_user_id: str) -> list[Food]:
        """List custom foods for one owner."""
        return [food for food in self.foods.values() if food.owner_user_id == owner_user_id]

    def get_custom_food(self, food_id: str, owner_user_id: str) -> Food | None:
        """Return a custom food only when it belongs to the requested owner."""
        food = self.foods.get(food_id)
        if food is None or food.owner_user_id != owner_user_id:
            return None
        return food

    def save_custom_food(self, food: Food) -> Food:
        """Save a custom food in memory."""
        self.foods[food.id] = food
        return food


def test_service_creates_and_updates_food_without_changing_its_id(
    custom_food_input: CustomFoodInput,
) -> None:
    """The service retains a food's ID when it updates its values."""
    repository: FoodRepository = InMemoryFoodRepository()
    service = CustomFoodService(repository, app_config.default_user_id)
    created_food = service.create_custom_food(custom_food_input)
    updated_food = service.update_custom_food(
        created_food.id,
        CustomFoodInput(name="Oats", nutrition_bases=custom_food_input.nutrition_bases),
    )

    assert updated_food.id == created_food.id
    assert updated_food.name == "Oats"


def test_service_raises_for_a_food_that_is_not_owned(custom_food_input: CustomFoodInput) -> None:
    """The service reports missing foods with a domain-level exception."""
    service = CustomFoodService(InMemoryFoodRepository(), app_config.default_user_id)

    with pytest.raises(CustomFoodNotFoundError):
        service.update_custom_food("missing-id", custom_food_input)
