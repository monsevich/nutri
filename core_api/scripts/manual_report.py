import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from ..db import async_session_factory
from ..models import User
from ..services.report_generator import generate_weekly_report


def current_week_range() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=6), today


async def main() -> None:
    week_start, week_end = current_week_range()
    async with async_session_factory() as session:
        users = await session.execute(select(User))
        for user in users.scalars():
            await generate_weekly_report(session, user, week_start, week_end)


if __name__ == "__main__":
    asyncio.run(main())
