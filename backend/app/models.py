from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.database import Base


class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True)

    url = Column(String, unique=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    health_checks = relationship("HealthCheck", back_populates="url")


class HealthCheck(Base):
    __tablename__ = "health_checks"
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    is_up = Column(Boolean)
    checked_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    url = relationship("URL", back_populates="health_checks")
