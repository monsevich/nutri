from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func

from ..db import async_session_factory
from ..models import DailyLog, User, WeeklyReport
from .report_generator import generate_weekly_report


scheduler = AsyncIOScheduler()


async def _should_generate_report(session, user: User, week_start: date) -> bool:
    existing = await session.execute(
        select(WeeklyReport).where(WeeklyReport.user_id == user.id, WeeklyReport.week_start == week_start)
    )
    if existing.scalars().first():
        return False
    first_log = await session.execute(
        select(func.min(DailyLog.date)).where(DailyLog.user_id == user.id)
    )
    first_log_date = first_log.scalar()
    return first_log_date is not None and first_log_date <= week_start


async def generate_reports_job() -> None:
    today = date.today()
    week_start = today - timedelta(days=6)
    week_end = today
    async with async_session_factory() as session:
        users = await session.execute(select(User))
        for user in users.scalars():
            if await _should_generate_report(session, user, week_start):
                await generate_weekly_report(session, user, week_start, week_end)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(generate_reports_job, "cron", hour=3, minute=0)
    scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
