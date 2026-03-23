# app/services/marker_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.marker import Marker
from app.models.photo import Photo

def create_marker_and_photo(
    db: Session, 
    latitude: float, 
    longitude: float, 
    category: str, 
    fake_s3_url: str
) -> Marker:
    """
    마커 및 연결된 사진 데이터를 생성합니다.
    """
    point_wkt = f"POINT({longitude} {latitude})"
    
    new_marker = Marker(
        category=category,
        location=point_wkt
    )
    db.add(new_marker)
    db.commit()
    db.refresh(new_marker)
    
    new_photo = Photo(
        marker_id=new_marker.id,
        s3_url=fake_s3_url
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    
    return new_marker


def get_markers_within_radius(db: Session, latitude: float, longitude: float, radius_meters: int = 1000):
    """
    반경(radius_meters) 이내의 마커 목록을 반환합니다.
    """
    center_point = f"POINT({longitude} {latitude})"
        
    query = db.query(
        Marker.id.label("id"),
        Marker.category.label("category"),
        func.ST_Y(func.ST_AsText(Marker.location)).label("latitude"),
        func.ST_X(func.ST_AsText(Marker.location)).label("longitude")
    ).filter(
        func.ST_DistanceSphere(Marker.location, func.ST_GeomFromText(center_point, 4326)) <= radius_meters 
    )
    
    return query.all()
