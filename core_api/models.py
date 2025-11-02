from datetime import date, datetime

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)
    height_cm = Column(Float, nullable=False)
    start_weight_kg = Column(Float, nullable=False)
    target_weight_kg = Column(Float, nullable=False)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    chronic_conditions = Column(JSON, nullable=True)
    activity_level = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    daily_logs = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")
    weekly_reports = relationship("WeeklyReport", back_populates="user", cascade="all, delete-orphan")
    menu_plans = relationship("MenuPlan", back_populates="user", cascade="all, delete-orphan")


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    calories_in = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    activity_level = Column(String, nullable=True)

    user = relationship("User", back_populates="daily_logs")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_weekly_reports_user_week"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    summary_text = Column(Text, nullable=False)
    status_flags = Column(JSON, nullable=False)

    user = relationship("User", back_populates="weekly_reports")


class MenuPlan(Base):
    __tablename__ = "menu_plans"
    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_menu_plans_user_week"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    menu_json = Column(JSON, nullable=False)

    user = relationship("User", back_populates="menu_plans")
