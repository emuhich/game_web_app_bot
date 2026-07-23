import os
import bcrypt
import logging
import uuid
from starlette.datastructures import UploadFile
from starlette.requests import Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select, func
from app.db.database import engine, async_session_maker
from app.db.models.users import User, Premium
from app.db.models.honesty import HonCategory, HonQuestion
from app.db.models.admin import Admin as AdminModel
from app.config import settings
from markupsafe import Markup
from sqladmin import BaseView, expose
from starlette.templating import Jinja2Templates
from pathlib import Path

logger = logging.getLogger(__name__)


class BasicAuth(AuthenticationBackend):
    async def login(self, request):
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            logger.warning("Login failed: empty username or password")
            return False
        if AdminModel is None:
            logger.error("AdminModel is not defined")
            return False
        async with async_session_maker() as session:
            result = await session.execute(select(AdminModel).where(AdminModel.username == username))
            admin = result.scalar_one_or_none()
            if not admin:
                logger.warning("Login failed: admin not found")
                return False
            if bcrypt.checkpw(password.encode(), admin.password.encode()):
                request.session["admin"] = username
                logger.info(f"Admin '{username}' logged in")
                return True
        logger.warning("Login failed: bad credentials")
        return False

    async def logout(self, request):
        user = request.session.pop("admin", None)
        if user:
            logger.info(f"Admin '{user}' logged out")

    async def authenticate(self, request):
        return bool(request.session.get("admin"))


class AdminUserAdmin(ModelView, model=AdminModel):
    """Управление записями админов через веб-панель.

    Позволяет создавать/редактировать админов, при этом пароль всегда хранится в виде bcrypt-хэша.
    """
    name = "Администратор"
    name_plural = "Администраторы"
    icon = "fas fa-user-shield"

    column_list = (AdminModel.id, AdminModel.username)
    column_searchable_list = ("username",)
    column_sortable_list = (AdminModel.id, AdminModel.username)
    column_default_sort = (AdminModel.id, False)

    # В формах разрешаем редактирование username и password, но в списке пароль не показываем
    form_columns = [AdminModel.username, AdminModel.password]

    async def insert_model(self, request: Request, data: dict):
        """При создании админа всегда хэшируем пароль перед сохранением."""
        raw_password = data.get("password")
        if raw_password:
            data["password"] = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk, data: dict):
        """При обновлении, если пароль указан — хэшируем его, иначе не трогаем существующий хэш."""
        raw_password = data.get("password")
        if raw_password:
            data["password"] = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        else:
            # если поле пароля пустое в форме, не переписываем его пустым значением
            data.pop("password", None)
        return await super().update_model(request, pk, data)


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fas fa-user"
    column_list = (User.telegram_id, User.first_name, User.username, User.is_active)
    column_searchable_list = ("first_name", "username")
    column_sortable_list = ("telegram_id",)


class PremiumAdmin(ModelView, model=Premium):
    name = "Премиум"
    name_plural = "Премиум"
    icon = "fas fa-crown"
    column_list = (Premium.id, Premium.user_id, Premium.purchase_date, Premium.expire_date, Premium.auto_renew)
    column_sortable_list = ("purchase_date", "expire_date")


# Отдельный форматтер для превью изображения категории, который возвращает безопасный HTML
# через Markup, чтобы sqladmin/Jinja не экранировали тег <img>

def category_image_preview_formatter(obj: HonCategory, _prop) -> str:
    url = getattr(obj, "image", None)
    if url:
        html = f'<img src="{url}" style="max-width:200px;max-height:120px;border-radius:10px;" />'
        return Markup(html)
    return ""


class HonCategoryAdmin(ModelView, model=HonCategory):
    name = "Категория"
    name_plural = "Категории"
    icon = "fas fa-layer-group"
    page_size = 25
    column_list = (
        HonCategory.id,
        HonCategory.name,
        HonCategory.order,
        HonCategory.is_visible,
        HonCategory.is_premium,
        HonCategory.is_adult,
        HonCategory.image,
        "image_preview",
    )
    column_formatters = {
        "image_preview": category_image_preview_formatter,
    }
    column_formatters_detail = column_formatters
    column_searchable_list = ("name",)
    column_sortable_list = (HonCategory.order, HonCategory.id)
    column_default_sort = (HonCategory.order, False)
    form_excluded_columns = [HonCategory.image]

    form_create_rules = (
        "name",
        "order",
        "is_visible",
        "is_premium",
        "is_adult",
        "upload_image",
    )
    form_edit_rules = (
        "name",
        "order",
        "is_visible",
        "is_premium",
        "is_adult",
        "image_preview_field",
        "upload_image",
    )
    form_detail_rules = (
        "id",
        "name",
        "order",
        "is_visible",
        "is_premium",
        "is_adult",
        "image_preview_field",
    )

    async def scaffold_form(self, form_rules=None):
        from wtforms import FileField
        from wtforms.validators import Optional as OptionalValidator
        form_class = await super().scaffold_form(form_rules)
        form_class.upload_image = FileField("Новое изображение категории", validators=[OptionalValidator()])
        return form_class

    def image_preview_field(self, obj: HonCategory) -> str:
        """Поле только для чтения в форме/детальном просмотре с текущей картинкой, если она есть."""
        url = getattr(obj, "image", None)
        if not url:
            return "(изображение не загружено)"
        html = f'<img src="{url}" style="max-width:260px;max-height:160px;border-radius:10px;display:block;margin-top:4px;" />'
        return Markup(html)

    async def insert_model(self, request: Request, data: dict):
        form = await request.form()
        file = form.get("upload_image")
        if isinstance(file, UploadFile):
            orig_name = getattr(file, "filename", "") or ""
            file_bytes = await file.read()
            if orig_name and file_bytes:
                filename = f"{uuid.uuid4().hex}"
                ext = os.path.splitext(orig_name)[1] or ".bin"
                safe_name = filename + ext
                media_dir = os.path.join(os.getcwd(), "media", "categories")
                os.makedirs(media_dir, exist_ok=True)
                target_path = os.path.join(media_dir, safe_name)
                with open(target_path, "wb") as f:
                    f.write(file_bytes)
                data["image"] = f"/media/categories/{safe_name}"
        data.pop("upload_image", None)
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk, data: dict):
        form = await request.form()
        file = form.get("upload_image")
        if isinstance(file, UploadFile):
            orig_name = getattr(file, "filename", "") or ""
            file_bytes = await file.read()
            if orig_name and file_bytes:
                filename = f"{uuid.uuid4().hex}"
                ext = os.path.splitext(orig_name)[1] or ".bin"
                safe_name = filename + ext
                media_dir = os.path.join(os.getcwd(), "media", "categories")
                os.makedirs(media_dir, exist_ok=True)
                target_path = os.path.join(media_dir, safe_name)
                with open(target_path, "wb") as f:
                    f.write(file_bytes)
                data["image"] = f"/media/categories/{safe_name}"
            else:
                data.pop("image", None)
        else:
            data.pop("image", None)
        data.pop("upload_image", None)
        return await super().update_model(request, pk, data)


# Кастомный фильтр по категории для вопросов, совместимый с текущей версией sqladmin
class HonQuestionCategoryFilter:
    key = "category_id"
    label = "Категория (ID)"

    @property
    def parameter_name(self) -> str:
        return self.key

    async def get_filtered_query(self, query, value, model):
        """Простейший фильтр по exact match category_id.

        sqladmin вызывает simple_filter.get_filtered_query(stmt, value, model),
        поэтому принимаем три аргумента и используем только query и value.
        """
        if not value:
            return query
        try:
            category_id = int(value)
        except (TypeError, ValueError):
            return query
        return query.where(HonQuestion.category_id == category_id)

    async def lookups(self, request, model, run_arbitrary_query):
        """Возвращаем список доступных вариантов (id, название категории) для выпадающего списка."""
        async with async_session_maker() as session:
            result = await session.execute(select(HonCategory.id, HonCategory.name).order_by(HonCategory.order))
            rows = result.all()
        return [(str(row.id), row.name) for row in rows]


class HonQuestionAdmin(ModelView, model=HonQuestion):
    name = "Вопрос"
    name_plural = "Вопросы"
    icon = "fas fa-question"
    page_size = 100
    column_list = (HonQuestion.id, HonQuestion.category, HonQuestion.text)
    column_sortable_list = (HonCategory.id, )
    column_default_sort = (HonQuestion.id, False)
    form_columns = [HonQuestion.category, HonQuestion.text]
    column_filters = [HonQuestionCategoryFilter()]


class DashboardRoot(BaseView):
    name = "Обзор"
    icon = "fas fa-chart-line"

    _templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / 'frontend' / 'templates'))

    @expose("/")
    async def index(self, request: Request):
        async with async_session_maker() as session:
            total_users = (await session.execute(select(func.count(User.telegram_id)))).scalar_one()
            premium_by_day = (
                await session.execute(
                    select(Premium.purchase_date, func.count(Premium.id))
                    .group_by(Premium.purchase_date)
                    .order_by(Premium.purchase_date)
                )
            ).all()
        premium_series = [
            {"date": row[0].strftime("%d.%m"), "count": row[1]} for row in premium_by_day
        ]
        context = {
            "request": request,
            "total_users": total_users,
            "premium_series": premium_series,
        }
        return self._templates.TemplateResponse("admin/dashboard.html", context)


def init_sqladmin(app) -> Admin:
    auth_backend = BasicAuth(secret_key=settings.ADMIN_SECRET)
    admin = Admin(app, engine, authentication_backend=auth_backend, base_url="/admin")
    # Регистрируем корневой дашборд первым — он будет открываться на /admin/
    admin.add_view(DashboardRoot)
    admin.add_view(AdminUserAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(PremiumAdmin)
    admin.add_view(HonCategoryAdmin)
    admin.add_view(HonQuestionAdmin)
    logger.info("sqladmin initialized")
    return admin
