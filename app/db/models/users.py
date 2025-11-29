from sqlalchemy import Integer, String, BigInteger, Boolean, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = 'users'
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    premium: Mapped['Premium'] = relationship(back_populates='user', uselist=False)


class Premium(Base):
    __tablename__ = 'premiums'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'))
    purchase_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Date] = mapped_column(Date, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped['User'] = relationship(back_populates='premium')
