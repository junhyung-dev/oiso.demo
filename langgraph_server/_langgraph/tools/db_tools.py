# (c) 2026 oiso.ai
from langchain_core.tools import tool
import math
import os
import json
from sqlalchemy import create_engine, text

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # 지구 반지름 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@tool
def search_nearby_stores(tag_name: str, lat: float, lng: float, radius_km: float = 1.0) -> str:
    """
    Search for nearby stores that sell a specific food or item based on a Korean tag.
    
    Args:
        tag_name (str): The Korean name of the food or item (e.g., "떡볶이", "김밥").
        lat (float): The latitude of the user's current location.
        lng (float): The longitude of the user's current location.
        radius_km (float): The search radius in kilometers (default is 1.0).
        
    Returns:
        str: A JSON-formatted string containing a list of nearby stores (name, distance, etc.),
             or a message indicating that no stores were found.
    """
    # 환경변수에서 직접 DB URL을 가져오거나 테스트된 내(표선) PostgreSQL 접속 주소를 사용
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # 입력받은 태그와 연관된 Store 정보들을 추출
            query = text('''
                SELECT s.id, s.name, s.latitude, s.longitude
                FROM stores s
                JOIN store_tag_association sta ON s.id = sta.store_id
                JOIN tags t ON sta.tag_id = t.id
                WHERE t.name = :tag_name
            ''')
            result = conn.execute(query, {"tag_name": tag_name}).fetchall()
            
            nearby_stores = []
            for row in result:
                store_lat = row[2] # latitude
                store_lng = row[3] # longitude
                
                # Haversine으로 유저 위치와 DB 매장 위치 사이의 실제 거리 계산
                distance = haversine(lat, lng, store_lat, store_lng)
                
                if distance <= radius_km:
                    nearby_stores.append({
                        "id": row[0],
                        "name": row[1],
                        "distance_km": round(distance, 2)
                    })
            
            # 거리가 가까운 순서대로 정렬 (오름차순)
            nearby_stores.sort(key=lambda x: x["distance_km"])
            
            if not nearby_stores:
                return f"No stores found within {radius_km}km for the tag '{tag_name}'."
            
            return json.dumps(nearby_stores, ensure_ascii=False)
            
    except Exception as e:
        return f"Error while searching the database: {str(e)}"
