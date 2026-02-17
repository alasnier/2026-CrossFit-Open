# infra/models.py
from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    sex = Column(String(10), nullable=False)
    birth_year = Column(Integer, nullable=False)
    level = Column(String(10), nullable=False)
    category = Column(String(20), nullable=False)
    _age = Column("age", Integer, nullable=False)
    scores = relationship("Score", back_populates="user", cascade="all, delete")

    @property
    def age(self) -> int:
        return datetime.now().year - self.birth_year

    @age.setter
    def age(self, value: int):
        self._age = value


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wod = Column(String(10), nullable=False)
    score = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    user = relationship("User", back_populates="scores")


class Wod(Base):
    __tablename__ = "wods"
    wod = Column(String(10), primary_key=True)
    label = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    timecap_seconds = Column(Integer, nullable=True)
