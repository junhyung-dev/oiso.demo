# app/models/marker.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.core.database import Base

class Marker(Base):
    """
    [DB 테이블: markers]
    마커 위치 및 카테고리 정보
    """
    __tablename__ = "markers"

    id = Column(Integer, primary_key=True, index=True)
    
    category = Column(String(50), nullable=False, index=True)
    
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    photos = relationship("Photo", back_populates="marker", cascade="all, delete-orphan")
