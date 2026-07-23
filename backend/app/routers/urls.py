from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", response_model=schemas.URLResponse)
def create_url(url: schemas.URLCreate, db: Session = Depends(get_db)):
    return crud.create_url(db=db, url=url)


@router.get("/", response_model=list[schemas.URLResponse])
def get_urls(db: Session = Depends(get_db)):
    return crud.get_urls(db)
