import bcrypt
import logging
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from app.db.database import engine, async_session_maker
from app.db.models.users import User, Premium
from app.db.models.honesty import HonCategory, HonQuestion
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from app.db.models.admin import Admin as AdminModel
except ImportError:
    AdminModel = None


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


# --- Вьюхи ---
class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fas fa-user"
    column_list = (User.telegram_id, User.first_name, User.username, User.is_active)
    column_searchable_list = (User.first_name, User.username)
    column_filters = (User.is_active,)
    column_sortable_list = (User.telegram_id,)


class PremiumAdmin(ModelView, model=Premium):
    name = "Премиум"
    name_plural = "Премиум"
    icon = "fas fa-crown"
    column_list = (Premium.id, Premium.user_id, Premium.purchase_date, Premium.expire_date, Premium.auto_renew)
    column_sortable_list = (Premium.purchase_date, Premium.expire_date)


class HonCategoryAdmin(ModelView, model=HonCategory):
    name = "Категория"
    name_plural = "Категории"
    icon = "fas fa-layer-group"
    column_list = (HonCategory.id, HonCategory.name, HonCategory.order, HonCategory.is_visible, HonCategory.is_premium,
                   HonCategory.is_adult)
    column_searchable_list = (HonCategory.name,)
    column_filters = (HonCategory.is_visible, HonCategory.is_premium, HonCategory.is_adult)
    column_sortable_list = (HonCategory.order,)


class HonQuestionAdmin(ModelView, model=HonQuestion):
    name = "Вопрос"
    name_plural = "Вопросы"
    icon = "fas fa-question"
    column_list = (HonQuestion.id, HonQuestion.category_id, HonQuestion.text, HonQuestion.order)
    column_sortable_list = (HonQuestion.order,)


def init_sqladmin(app) -> Admin:
    auth_backend = BasicAuth(secret_key=settings.ADMIN_SECRET)
    admin = Admin(app, engine, authentication_backend=auth_backend, base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(PremiumAdmin)
    admin.add_view(HonCategoryAdmin)
    admin.add_view(HonQuestionAdmin)
    logger.info("sqladmin initialized")
    return admin
