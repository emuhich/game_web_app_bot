from fastapi import APIRouter, HTTPException
from app.api.dao import ApplicationDAO, ServiceDAO, MasterDAO, UserDAO
from app.api.schemas import ApplicationCreate, ApplicationRead, ServiceRead, MasterRead, ApplicationListItem, ApplicationReschedule
from app.api.models import User
from app.database import async_session_maker
from sqlalchemy.exc import SQLAlchemyError
from app.bot.create_bot import bot
from app.config import settings

router = APIRouter(prefix='/api', tags=['API'])

ADMIN_ID = settings.ADMIN_ID


@router.get('/services', response_model=list[ServiceRead])
async def get_services():
    services = await ServiceDAO.find_all()
    return services


@router.get('/masters', response_model=list[MasterRead])
async def get_masters():
    masters = await MasterDAO.find_all()
    return masters


@router.get('/applications/{user_id}', response_model=list[ApplicationListItem])
async def list_user_applications(user_id: int):
    data = await ApplicationDAO.get_applications_by_user(user_id)
    return data or []


@router.delete('/applications/{application_id}', status_code=204)
async def cancel_application(application_id: int):
    ok = await ApplicationDAO.cancel_application(application_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Заявка не найдена')
    # Уведомление админу об отмене
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"❌ Заявка #{application_id} отменена пользователем")
    except Exception:
        pass
    return None


@router.patch('/applications/{application_id}/reschedule', status_code=200)
async def reschedule_application(application_id: int, payload: ApplicationReschedule):
    ok = await ApplicationDAO.reschedule_application(application_id, payload.appointment_date, payload.appointment_time)
    if not ok:
        raise HTTPException(status_code=404, detail='Заявка не найдена')
    # Уведомление админу о переносе
    try:
        await bot.send_message(chat_id=ADMIN_ID,
                               text=(f"🔄 Заявка #{application_id} перенесена\n"
                                     f"📅 Новая дата: {payload.appointment_date}\n"
                                     f"⏰ Новое время: {payload.appointment_time}"))
    except Exception:
        pass
    return {"status": "ok"}


@router.post('/applications', response_model=ApplicationRead, status_code=201)
async def create_application(payload: ApplicationCreate):
    # Ensure user exists or create placeholder user if user_id > 0 and not found
    if payload.user_id and payload.user_id > 0:
        user = await UserDAO.find_one_or_none(telegram_id=payload.user_id)
        if user is None:
            async with async_session_maker() as session:
                new_user = User(telegram_id=payload.user_id, first_name=payload.client_name, username="")
                session.add(new_user)
                try:
                    await session.commit()
                    await session.refresh(new_user)
                except SQLAlchemyError:
                    await session.rollback()
                    raise HTTPException(status_code=500, detail='Не удалось создать пользователя')
    try:
        app_obj = await ApplicationDAO.add(
            user_id=payload.user_id if payload.user_id else None,
            master_id=payload.master_id,
            service_id=payload.service_id,
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time,
            gender=payload.gender,
            client_name=payload.client_name
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail='Ошибка базы данных') from e

    # Получаем мастера и услугу для сообщения
    master = await MasterDAO.find_one_or_none(master_id=payload.master_id)
    service = await ServiceDAO.find_one_or_none(service_id=payload.service_id)
    master_name = master.master_name if master else 'Неизвестно'
    service_name = service.service_name if service else 'Неизвестно'
    gender_map = {"male": "Мужской", "female": "Женский"}
    gender_name = gender_map.get(payload.gender, payload.gender)

    admin_message = (
        "🔔 <b>Новая запись!</b>\n\n"
        "📄 <b>Детали заявки:</b>\n"
        f"👤 Имя клиента: {payload.client_name}\n"
        f"💇 Услуга: {service_name}\n"
        f"✂️ Мастер: {master_name}\n"
        f"📅 Дата: {payload.appointment_date}\n"
        f"⏰ Время: {payload.appointment_time}\n"
        f"🧑‍🦰 Пол клиента: {gender_name}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='HTML')
    except Exception:
        pass

    return app_obj
