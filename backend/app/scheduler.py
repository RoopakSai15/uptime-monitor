from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import URL
from app.crud import save_health_check
from app.services.ping import check_url

scheduler = AsyncIOScheduler()


async def check_and_store(db: Session, url: URL):
    """Ping a single URL and persist the result. Shared by the periodic
    job and the manual /check-now endpoint so there's one code path."""
    result = await check_url(url.url)
    return save_health_check(db, url.id, result)


async def monitor_urls():
    db: Session = SessionLocal()

    try:
        urls = db.query(URL).all()

        for url in urls:
            result = await check_url(url.url)

            save_health_check(db, url.id, result)

    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        monitor_urls,
        "interval",
        minutes=1,
    )

    scheduler.start()
