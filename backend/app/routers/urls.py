from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.scheduler import check_and_store

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", response_model=schemas.URLResponse)
async def create_url(url: schemas.URLCreate, db: Session = Depends(get_db)):
    db_url = crud.create_url(db=db, url=url)
    # Immediate check so the dashboard doesn't show "unknown" for up to a minute.
    await check_and_store(db, db_url)
    return crud.url_with_latest_check(db, db_url)


@router.get("/", response_model=list[schemas.URLResponse])
def get_urls(db: Session = Depends(get_db)):
    urls = crud.get_urls(db)
    return [crud.url_with_latest_check(db, u) for u in urls]


@router.delete("/{url_id}", status_code=204)
def delete_url(url_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_url(db, url_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return None


@router.get("/{url_id}/history", response_model=list[schemas.HealthCheckResponse])
def url_history(url_id: int, limit: int = 50, db: Session = Depends(get_db)):
    db_url = crud.get_url(db, url_id)
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return crud.get_history(db, url_id, limit=limit)


@router.post("/{url_id}/check-now", response_model=schemas.URLResponse)
async def check_now(url_id: int, db: Session = Depends(get_db)):
    db_url = crud.get_url(db, url_id)
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    await check_and_store(db, db_url)
    return crud.url_with_latest_check(db, db_url)
