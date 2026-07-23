from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.routers.urls import router as url_router
from app.scheduler import start_scheduler, scheduler

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="Uptime Monitor API",
    version="1.0.0",
    description="Backend API for monitoring website uptime.",
    lifespan=lifespan,
)

app.include_router(url_router)


@app.get("/")
def root():
    return {"message": "Uptime Monitor API is running."}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
