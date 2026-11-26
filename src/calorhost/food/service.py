from dataclasses import dataclass
from typing import Any

import requests

from ..config import Config

config = Config()


class FoodService:
    """Service for interacting with data source to search for foods"""

    def text_search(self, name: str) -> list[Food]:
        """Search Open Food Facts using Search-a-licious."""
        search_query = (
            f'countries:"en:{config.country}" AND ({name}) '
            "AND (nutriments.energy-kcal_100g:[* TO *] OR nutriments.energy-kj_100g:[* TO *]) "
            "AND nutriments.proteins_100g:[* TO *] "
            "AND nutriments.carbohydrates_100g:[* TO *] "
            "AND nutriments.fat_100g:[* TO *]"
        )

        response = requests.post(
            config.search_api_url,
            headers={"User-Agent": config.user_agent},
            json={
                "q": search_query,
                "page": 1,
                "page_size": 20,
                "langs": ["en"],
                "boost_phrase": True,
                "fields": [
                    "code",
                    "product_name",
                    "product_name_en",
                    "nutriments",
                    "serving_quantity",
                    "serving_quantity_unit",
                ],
            },
            timeout=10,
        )

        response.raise_for_status()
        hits = response.json().get("hits", [])

        food_results: list[Food] = []
        for hit in hits:
            nutriments = hit.get("nutriments") or {}
            serving_quantity = hit.get("serving_quantity")

            food = Food(
                name=hit.get("product_name_en") or hit.get("product_name", "unknown"),
                calories=self._calories_value(nutriments, serving_quantity),
                protein=self._nutriment_value(nutriments, "proteins", serving_quantity),
                carbohydrates=self._nutriment_value(nutriments, "carbohydrates", serving_quantity),
                fats=self._nutriment_value(nutriments, "fat", serving_quantity),
                serving_quantity=serving_quantity,
                service_quantity_unit=hit.get("serving_quantity_unit"),
            )

            food_results.append(food)

        return food_results

    @classmethod
    def _calories_value(cls, nutriments: dict[str, Any], serving_quantity: Any) -> int:
        """Read kcal directly, or convert the indexed kJ value to kcal."""
        for key in ("energy-kcal_serving", "energy-kcal_100g"):
            value = nutriments.get(key)
            if value is not None:
                return round(float(cls._nutriment_value(nutriments, "energy-kcal", serving_quantity)))
        return round(float(cls._nutriment_value(nutriments, "energy-kj", serving_quantity)) / 4.184)

    @staticmethod
    def _nutriment_value(nutriments: dict[str, Any], nutrient: str, serving_quantity: Any) -> Any:
        """Use per-serving data or scale indexed per-100g nutrition to the serving."""
        serving_value = nutriments.get(f"{nutrient}_serving")
        if serving_value is not None:
            return serving_value
        per_100g_value = nutriments.get(f"{nutrient}_100g")
        if per_100g_value is None:
            return 0
        if serving_quantity is None:
            return per_100g_value
        try:
            return float(per_100g_value) * float(serving_quantity) / 100
        except TypeError, ValueError:
            return per_100g_value


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
