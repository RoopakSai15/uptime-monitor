from sqlalchemy.orm import Session

from app import models, schemas


def create_url(db: Session, url: schemas.URLCreate):
    db_url = models.URL(url=str(url.url))

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return db_url


def get_urls(db: Session):
    return db.query(models.URL).all()


def save_health_check(db: Session, url_id, result):

    check = models.HealthCheck(
        url=url_id,
        status_code=result["status_code"],
        response_time_ms=result["response_time_ms"],
        is_up=result["is_up"],
    )

    db.add(check)
    db.commit()
