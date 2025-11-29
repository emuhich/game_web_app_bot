from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


# Пользователи
class UserNotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Пользователь не найден"


class PremiumNotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Премиум не найден"


class PremiumDurationInvalidException(BaseHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Некорректная длительность премиума"


# Игры
class GameNotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Игра не найдена"


class CategoryNotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Категория не найдена"


class QuestionNotFoundException(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Вопрос не найден"


__all__ = [
    'UserNotFoundException',
    'PremiumNotFoundException',
    'PremiumDurationInvalidException',
    'GameNotFoundException',
    'CategoryNotFoundException',
    'QuestionNotFoundException'
]
