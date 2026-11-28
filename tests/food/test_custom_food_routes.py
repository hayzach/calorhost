"""Tests for custom-food pages and form submission."""

import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from calorhost.app_config import AppConfig
from calorhost.food.orm_models import FoodRow

app_config = AppConfig()


def test_create_edit_and_list_custom_food(client: TestClient) -> None:
    """A custom food can be created, edited, and listed."""
    form_values = {
        "name": "Rice",
        "per_100g_energy": "0",
        "per_100g_energy_unit": "kcal",
        "per_100g_protein": "0",
        "per_100g_fat": "0",
        "per_100g_carbohydrates": "0",
        "per_100g_fiber": "",
    }

    response = client.post("/foods/custom", data=form_values, follow_redirects=False)

    assert response.status_code == 303
    catalog_response = client.get("/foods/custom")
    assert catalog_response.status_code == 200
    assert "Rice" in catalog_response.text

    match = re.search(r'href="/foods/custom/([^/]+)/edit"', catalog_response.text)
    assert match is not None
    edit_url = match.group(1)
    edit_response = client.get(f"/foods/custom/{edit_url}/edit")
    assert edit_response.status_code == 200
    assert 'value="0"' in edit_response.text
    assert f'hx-patch="/foods/custom/{edit_url}"' in edit_response.text

    form_values["name"] = "Brown rice"
    update_response = client.patch(f"/foods/custom/{edit_url}", data=form_values)

    assert update_response.status_code == 200
    assert "Food saved." in update_response.text
    assert "Brown rice" in client.get("/foods/custom").text


def test_incomplete_required_nutrients_return_form_errors(client: TestClient) -> None:
    """The form is redisplayed with errors when required nutrients are incomplete."""
    response = client.post(
        "/foods/custom",
        data={
            "name": "Incomplete",
            "per_100g_energy": "100",
            "per_100g_protein": "2",
            "per_100g_fat": "",
            "per_100g_carbohydrates": "",
        },
    )

    assert response.status_code == 422
    assert "Each nutrition basis must include energy, protein, fat, and carbohydrates" in response.text
    assert 'value="Incomplete"' in response.text


def test_create_rejects_values_outside_storage_range(client: TestClient) -> None:
    """Values that cannot fit the database are returned as form validation errors."""
    response = client.post(
        "/foods/custom",
        data={
            "name": "Impossible energy",
            "per_100g_energy": "10000000000000",
            "per_100g_protein": "1",
            "per_100g_fat": "1",
            "per_100g_carbohydrates": "1",
        },
    )

    assert response.status_code == 422
    assert "Enter a value no greater than 9,223,372,036,854.775807." in response.text


def test_new_custom_food_form_shows_nutrition_options(client: TestClient) -> None:
    """The blank custom-food form shows its available nutrition options."""
    response = client.get("/foods/custom/new")

    assert response.status_code == 200
    assert "Per 100 g" in response.text
    assert "Per serving" in response.text
    assert "Serving conversion (optional)" in response.text


def test_created_custom_food_belongs_to_the_default_user(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """New custom foods are assigned to the configured user."""
    response = client.post(
        "/foods/custom",
        data={
            "name": "Rice",
            "per_100g_energy": "100",
            "per_100g_protein": "2",
            "per_100g_fat": "1",
            "per_100g_carbohydrates": "20",
        },
        follow_redirects=False,
    )
    with test_session_factory() as session:
        food = session.scalar(select(FoodRow))

    assert response.status_code == 303
    assert food is not None
    assert food.owner_user_id == app_config.default_user_id


def test_patch_validation_returns_an_error_form_fragment(client: TestClient) -> None:
    """Invalid PATCH requests return an HTMX-compatible form with field errors."""
    client.post(
        "/foods/custom",
        data={
            "name": "Rice",
            "per_100g_energy": "100",
            "per_100g_protein": "2",
            "per_100g_fat": "1",
            "per_100g_carbohydrates": "20",
        },
    )
    catalog_response = client.get("/foods/custom")
    match = re.search(r'href="/foods/custom/([^/]+)/edit"', catalog_response.text)
    assert match is not None

    response = client.patch(
        f"/foods/custom/{match.group(1)}",
        data={
            "name": "Rice",
            "per_100g_energy": "100",
            "per_100g_protein": "2",
            "per_100g_fat": "",
            "per_100g_carbohydrates": "",
        },
    )

    assert response.status_code == 422
    assert "Each nutrition basis must include energy, protein, fat, and carbohydrates" in response.text
    assert f'hx-patch="/foods/custom/{match.group(1)}"' in response.text
