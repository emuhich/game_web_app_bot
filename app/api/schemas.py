from datetime import date, time
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ApplicationCreate(BaseModel):
    user_id: int = Field(ge=0)
    master_id: int
    service_id: int
    appointment_date: date
    appointment_time: time
    gender: str
    client_name: str

    @field_validator('gender')
    def validate_gender(cls, v: str):
        if v not in {'male', 'female'}:
            raise ValueError('gender must be male or female')
        return v


class ApplicationRead(BaseModel):
    id: int
    user_id: Optional[int]
    master_id: int
    service_id: int
    appointment_date: date
    appointment_time: time
    gender: str
    client_name: str

    class Config:
        from_attributes = True


class ServiceRead(BaseModel):
    service_id: int
    service_name: str

    class Config:
        from_attributes = True


class MasterRead(BaseModel):
    master_id: int
    master_name: str

    class Config:
        from_attributes = True


class ApplicationListItem(BaseModel):
    application_id: int
    service_name: str
    master_name: str
    appointment_date: date
    appointment_time: time
    gender: str


class ApplicationReschedule(BaseModel):
    appointment_date: date
    appointment_time: time

    @field_validator('appointment_date')
    def validate_date(cls, v: date):
        from datetime import date as _d
        if v < _d.today():
            raise ValueError('Дата не может быть в прошлом')
        return v
