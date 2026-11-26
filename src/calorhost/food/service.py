import logging
from dataclasses import dataclass
from typing import Any

import requests
from openfoodfacts import API as OFF_API
from openfoodfacts import APIVersion, Country, Environment

SEARCH_API_URL = "https://search.openfoodfacts.org/search"
PRODUCT_SEARCH_API_URL = "https://world.openfoodfacts.org/api/v2/search"
USER_AGENT = "CalorHost/0.1.0"
REQUEST_TIMEOUT = 10
PRODUCT_DETAIL_FIELDS = (
    "code",
    "product_name",
    "product_name_en",
    "nutriments",
    "serving_size",
    "serving_quantity",
    "serving_quantity_unit",
)
logger = logging.getLogger(__name__)


class FoodService:
    """Service for interacting with data source to search for foods"""

    api: OFF_API

    def __init__(self) -> None:
        self.api = OFF_API(
            user_agent=USER_AGENT,
            environment=Environment.org,
            version=APIVersion.v3,
            country=Country.au,
        )

    def text_search(self, name: str) -> list[Food]:
        """Search Open Food Facts using Search-a-licious."""
        response = requests.post(
            SEARCH_API_URL,
            headers={"User-Agent": USER_AGENT},
            json={
                "q": f'countries_tags:"en:australia" AND ({name})',
                "page": 1,
                "page_size": 20,
                "langs": ["en"],
                "boost_phrase": True,
                "fields": ["code", "product_name", "product_name_en", "nutriments"],
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])

        # Search-a-licious is optimized for discovery and may not index serving
        # nutrition fields. Hydrate its hits in one request to preserve the
        # serving-level values previously returned by Product Opener.
        products_by_code = self._fetch_product_details(hits)

        food_results: list[Food] = []
        for hit in hits:
            product = products_by_code.get(str(hit.get("code", "")), hit)
            nutriments = product.get("nutriments") or {}

            food = Food(
                name=product.get("product_name_en") or product.get("product_name", "unknown"),
                calories=self._nutriment_value(nutriments, "energy-kcal"),
                protein=self._nutriment_value(nutriments, "proteins"),
                carbohydrates=self._nutriment_value(nutriments, "carbohydrates"),
                fats=self._nutriment_value(nutriments, "fat"),
            )

            food_results.append(food)

        return food_results

    @staticmethod
    def _nutriment_value(nutriments: dict[str, Any], nutrient: str) -> Any:
        """Prefer per-serving data, falling back to the indexed per-100g value."""
        serving_value = nutriments.get(f"{nutrient}_serving")
        if serving_value is not None:
            return serving_value
        return nutriments.get(f"{nutrient}_100g", 0)

    @staticmethod
    def _fetch_product_details(hits: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Fetch full Product Opener records for Search-a-licious hits in one call."""
        codes = list(dict.fromkeys(str(hit["code"]) for hit in hits if hit.get("code")))
        if not codes:
            return {}

        params: dict[str, str | int] = {
            "code": ",".join(codes),
            "fields": ",".join(PRODUCT_DETAIL_FIELDS),
            "page_size": len(codes),
        }
        try:
            response = requests.get(
                PRODUCT_SEARCH_API_URL,
                headers={"User-Agent": USER_AGENT},
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            products = response.json().get("products", [])
        except (requests.RequestException, ValueError, AttributeError) as error:
            logger.warning("Could not hydrate Open Food Facts search results: %s", error)
            return {}

        return {str(product["code"]): product for product in products if product.get("code")}

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
