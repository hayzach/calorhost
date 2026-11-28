import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .food.custom_food_routes import router as custom_food_router
from .food.service import FoodService
from .templates import templates

app = FastAPI()

app.include_router(custom_food_router)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request) -> HTMLResponse:
    """Serve the main HTML page"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/off-api-text-search", response_class=HTMLResponse)
async def off_api_text_search(request: Request) -> HTMLResponse:
    """Use text to search for packaged foods using the open food facts api"""
    food_service = FoodService()

    form_data = await request.form()
    food_name = form_data.get("food_name")
    if not isinstance(food_name, str) or not food_name.strip():
        raise HTTPException(status_code=422, detail="food_name must be a non-empty string")

    food_results = food_service.text_search(food_name)

    context = {"food_name": food_name, "food_results": food_results}

    return templates.TemplateResponse(request=request, name="food-search-results.html", context=context)


@app.post("/off-api-label-search", response_class=HTMLResponse)
async def off_api_label_search(request: Request) -> HTMLResponse:
    """Use a label to search for a packaged food using the open food facts api"""
    food_service = FoodService()

    form_data = await request.form()
    label = form_data.get("label")
    if not isinstance(label, str) or not label.strip():
        raise HTTPException(status_code=422, detail="label must be a non-empty string")

    food_results = food_service.text_search(label)

    context = {"food_name": label, "food_results": food_results}

    return templates.TemplateResponse(request=request, name="food-search-results.html", context=context)


def run() -> None:
    """entrypoint for app"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
