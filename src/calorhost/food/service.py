from dataclasses import dataclass

from openfoodfacts import API as OffApi
from openfoodfacts import Environment


class FoodService:
    """Service for interacting with data source to search for foods"""

    api: OffApi

    def __init__(self):
        self.api = OffApi(user_agent="CalorHost", environment=Environment.org)

    def text_search(self, name: str) -> list[Food]:
        """Search open food facts api for a list of foods like 'name'"""
        breakpoint()
        product_results = self.api.product.text_search(name)

        food_results: list[Food] = []
        for product in product_results["products"]:
            nutriments = product.get("nutriments", {})

            food = Food(
                name=product.get("product_name", "unknown"),
                calories=nutriments.get("energy-kcal_serving", 0),
                protein=nutriments.get("proteins_serving", 0),
                carbohydrates=nutriments.get("carbohydrates_serving", 0),
                fats=nutriments.get("fat_serving", 0),
            )

            food_results.append(food)

        return food_results

    # def label_search(self, label: str) -> Food:
    #     product = self.api.product.get(label)
    #
    #     return product


@dataclass
class Food:
    """Class to represent a food"""

    name: str
    calories: int
    protein: float
    carbohydrates: float
    fats: float
    serving_quantity: float | None = None
    service_quantity_unit: str | None = None
