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


def get_url(db: Session, url_id: int):
    return db.query(models.URL).filter(models.URL.id == url_id).first()


def delete_url(db: Session, url_id: int):
    db_url = get_url(db, url_id)
    if db_url is None:
        return None
    db.delete(db_url)
    db.commit()
    return db_url


def get_latest_check(db: Session, url_id: int):
    return (
        db.query(models.HealthCheck)
        .filter(models.HealthCheck.url_id == url_id)
        .order_by(models.HealthCheck.checked_at.desc())
        .first()
    )


def get_history(db: Session, url_id: int, limit: int = 50):
    return (
        db.query(models.HealthCheck)
        .filter(models.HealthCheck.url_id == url_id)
        .order_by(models.HealthCheck.checked_at.desc())
        .limit(limit)
        .all()
    )


def save_health_check(db: Session, url_id, result):
    # url_id=url_id, NOT url=url_id. `url` is the ORM relationship
    # (expects a URL object); `url_id` is the actual FK column. Passing
    # a raw int into `url` throws AttributeError: 'int' object has no
    # attribute '_sa_instance_state' the moment SQLAlchemy tries to
    # treat it as a related object — this was crashing your scheduler.
    check = models.HealthCheck(
        url_id=url_id,
        status_code=result["status_code"],
        response_time_ms=result["response_time_ms"],
        is_up=result["is_up"],
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def url_with_latest_check(db: Session, db_url: models.URL) -> schemas.URLResponse:
    """Flatten a URL row + its latest HealthCheck into one response object."""
    latest = get_latest_check(db, db_url.id)
    return schemas.URLResponse(
        id=db_url.id,
        url=db_url.url,
        created_at=db_url.created_at,
        is_up=latest.is_up if latest else None,
        status_code=latest.status_code if latest else None,
        response_time_ms=latest.response_time_ms if latest else None,
        last_checked_at=latest.checked_at if latest else None,
    )
