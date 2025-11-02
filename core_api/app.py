import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import init_db
from .routers import log, menu, progress, profile, report
from .services.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()


app = FastAPI(title="Core Nutrition API", lifespan=lifespan)
app.include_router(profile.router)
app.include_router(log.router)
app.include_router(progress.router)
app.include_router(menu.router)
app.include_router(report.router)


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
