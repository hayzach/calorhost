from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/off-api-food-search", response_class=HTMLResponse)
async def off_api_food_search(request: Request):
    """Search for packaged food using the open food facts api"""
    form_data = await request.form()

    food_value = form_data.get("food")

    context = {
        "food": food_value,
    }

    return templates.TemplateResponse(request=request, name="food-search-results.html", context=context)


def run():
    """entrypoint for app"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
