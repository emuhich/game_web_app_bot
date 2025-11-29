from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix='', tags=['Фронтенд'])
templates = Jinja2Templates(directory='app-v-1/templates')


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html",
                                      {"request": request, "title": "Элегантная парикмахерская"})


@router.get("/form", response_class=HTMLResponse)
async def get_form(request: Request, user_id: int | None = None, first_name: str | None = None):
    return templates.TemplateResponse("form.html", {"request": request, "user_id": user_id, "first_name": first_name})


@router.get("/applications", response_class=HTMLResponse)
async def get_applications_page(request: Request, user_id: int | None = None):
    # user_id будет извлечен из Telegram initData на фронте, но если пришел в query — передаем
    return templates.TemplateResponse("applications.html", {"request": request, "user_id": user_id})
