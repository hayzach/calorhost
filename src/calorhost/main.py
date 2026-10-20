from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .food.service import FoodService

app = FastAPI()

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/off-api-text-search", response_class=HTMLResponse)
async def off_api_text_search(request: Request):
    """Use text to search for packaged foods using the open food facts api"""
    food_service = FoodService()

    form_data = await request.form()
    food_name = form_data.get("food_name")

    food_results = food_service.text_search(food_name)

    context = {"food_name": food_name, "food_results": food_results}

    return templates.TemplateResponse(request=request, name="food-search-results.html", context=context)


@app.post("/off-api-label-search", response_class=HTMLResponse)
async def off_api_label_search(request: Request):
    """Use a label to search for a packaged food using the open food facts api"""
    food_service = FoodService()

    form_data = await request.form()
    label = form_data.get("label")

    food = food_service.label_search(label)

    context = {
        "food_name": food.product_name,
        "protein": food.protein,
        "carbohydrates": food.carbohydrates,
        "fat": food.fat,
    }

    return templates.TemplateResponse(request=request, name="food-search-results.html", context=context)


def run():
    """entrypoint for app"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()


# "9345105000809"
