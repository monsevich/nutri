from fastapi import FastAPI

from app.routers import auth, tenants, clients, services, staff, appointments, deals
from app.ai.router import router as ai_router

app = FastAPI(title="Tenant Scheduler API")

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(clients.router)
app.include_router(services.router)
app.include_router(staff.router)
app.include_router(appointments.router)
app.include_router(deals.router)
app.include_router(ai_router)


@app.get("/")
def read_root():
    return {"status": "ok"}
