"""Application operations for custom foods."""

from .domain import CustomFoodInput, Food
from .repository import FoodRepository


class CustomFoodNotFoundError(LookupError):
    """Raised when a custom food does not exist for the current user."""

    def __init__(self, food_id: str) -> None:
        self.food_id = food_id
        super().__init__(f"Custom food {food_id!r} was not found.")


class CustomFoodService:
    """Create, update, and retrieve custom foods."""

    def __init__(self, repository: FoodRepository, owner_user_id: str) -> None:
        """Create a service for one user's foods."""
        self._repository = repository
        self._owner_user_id = owner_user_id

    def list_custom_foods(self) -> list[Food]:
        """Return all custom foods for the configured user."""
        return self._repository.list_custom_foods(self._owner_user_id)

    def get_custom_food(self, food_id: str) -> Food:
        """Return a custom food or raise when it is unavailable."""
        food = self._repository.get_custom_food(food_id, self._owner_user_id)
        if food is None:
            raise CustomFoodNotFoundError(food_id)
        return food

    def create_custom_food(self, food_input: CustomFoodInput) -> Food:
        """Validate and save a custom food."""
        food = Food.create_custom(self._owner_user_id, food_input)
        return self._repository.save_custom_food(food)

    def update_custom_food(self, food_id: str, food_input: CustomFoodInput) -> Food:
        """Validate and update an existing custom food."""
        existing_food = self.get_custom_food(food_id)
        food = Food.create_custom(self._owner_user_id, food_input, food_id=existing_food.id)
        return self._repository.save_custom_food(food)
