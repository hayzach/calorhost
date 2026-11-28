"""HTTP routes for custom-food management."""

from collections.abc import Mapping
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from ..app_config import AppConfig
from ..db import get_session
from ..templates import templates
from .custom_food_service import CustomFoodNotFoundError, CustomFoodService
from .domain import NUTRIENT_DEFINITIONS, Food, FoodValidationError
from .forms import form_values_from_food, parse_custom_food_form
from .repository import SqlAlchemyFoodRepository

router = APIRouter(prefix="/foods/custom", tags=["custom foods"])
app_config = AppConfig()


def get_custom_food_service(session: Annotated[Session, Depends(get_session)]) -> CustomFoodService:
    """Build a service for the single default user."""
    return CustomFoodService(SqlAlchemyFoodRepository(session), app_config.default_user_id)


@router.get("", response_class=HTMLResponse)
def list_custom_foods(
    request: Request,
    service: Annotated[CustomFoodService, Depends(get_custom_food_service)],
) -> HTMLResponse:
    """Render the custom-food catalog."""
    return templates.TemplateResponse(
        request=request,
        name="foods/custom_food_list.html",
        context={"foods": service.list_custom_foods()},
    )


@router.get("/new", response_class=HTMLResponse)
def new_custom_food(request: Request) -> HTMLResponse:
    """Render a blank custom-food form."""
    return _render_form(
        request,
        values={
            "per_100g_energy_unit": "kcal",
            "per_serving_energy_unit": "kcal",
            "serving_unit": "g",
        },
    )


@router.post("", response_class=HTMLResponse)
async def create_custom_food(
    request: Request,
    service: Annotated[CustomFoodService, Depends(get_custom_food_service)],
) -> Response:
    """Validate and create a custom food."""
    values = await _form_values(request)
    try:
        food_input = parse_custom_food_form(values)
        service.create_custom_food(food_input)
    except FoodValidationError as error:
        return _render_form(request, values=values, field_errors=error.field_errors, status_code=422)
    return RedirectResponse(url="/foods/custom", status_code=303)


@router.get("/{food_id}/edit", response_class=HTMLResponse)
def edit_custom_food(
    food_id: str,
    request: Request,
    service: Annotated[CustomFoodService, Depends(get_custom_food_service)],
) -> HTMLResponse:
    """Render a custom-food form populated with saved values."""
    try:
        food = service.get_custom_food(food_id)
    except CustomFoodNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _render_form(request, values=form_values_from_food(food), food=food)


@router.patch("/{food_id}", response_class=HTMLResponse)
async def update_custom_food(
    food_id: str,
    request: Request,
    service: Annotated[CustomFoodService, Depends(get_custom_food_service)],
) -> HTMLResponse:
    """Validate and update a custom food."""
    values = await _form_values(request)
    try:
        food_input = parse_custom_food_form(values)
        food = service.update_custom_food(food_id, food_input)
    except FoodValidationError as error:
        return _render_form_fragment(
            request,
            values=values,
            field_errors=error.field_errors,
            food_id=food_id,
            success_message=None,
            status_code=422,
        )
    except CustomFoodNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _render_form_fragment(
        request,
        values=form_values_from_food(food),
        field_errors={},
        food_id=food.id,
        success_message="Food saved.",
        status_code=200,
    )


async def _form_values(request: Request) -> dict[str, str]:
    """Read string values from a submitted form."""
    form_data = await request.form()
    return {key: value for key, value in form_data.multi_items() if isinstance(value, str)}


def _render_form(
    request: Request,
    values: Mapping[str, str],
    field_errors: Mapping[str, str] | None = None,
    food: Food | None = None,
    food_id: str | None = None,
    status_code: int | None = None,
) -> HTMLResponse:
    """Render the custom-food form for creation or editing."""
    if field_errors is None:
        field_errors = {}
    if status_code is None:
        status_code = 200
    if food is not None:
        food_id = food.id

    return templates.TemplateResponse(
        request=request,
        name="foods/custom_food_form.html",
        context={
            "field_errors": field_errors,
            "food_id": food_id,
            "form_values": values,
            "nutrients": NUTRIENT_DEFINITIONS,
            "title": "Edit custom food" if food_id is not None else "Create custom food",
        },
        status_code=status_code,
    )


def _render_form_fragment(
    request: Request,
    values: Mapping[str, str],
    field_errors: Mapping[str, str],
    food_id: str,
    success_message: str | None,
    status_code: int,
) -> HTMLResponse:
    """Render an updated custom-food form fragment for HTMX."""
    return templates.TemplateResponse(
        request=request,
        name="foods/custom_food_form_fields.html",
        context={
            "field_errors": field_errors,
            "food_id": food_id,
            "form_values": values,
            "nutrients": NUTRIENT_DEFINITIONS,
            "success_message": success_message,
        },
        status_code=status_code,
    )
