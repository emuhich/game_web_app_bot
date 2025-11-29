from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging
from typing import Optional

router = APIRouter(prefix='', tags=['Фронтенд'])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'
if not TEMPLATES_DIR.exists():
    logging.warning(f"Templates directory not found: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Элегантная парикмахерская"}
    )


@router.get("/form", response_class=HTMLResponse)
async def get_form(request: Request, user_id: Optional[int] = None, first_name: Optional[str] = None):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "user_id": user_id, "first_name": first_name}
    )


@router.get("/applications", response_class=HTMLResponse)
async def get_applications_page(request: Request, user_id: Optional[int] = None):
    return templates.TemplateResponse(
        "applications.html",
        {"request": request, "user_id": user_id}
    )
