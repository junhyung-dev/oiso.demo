from db.session import SessionLocal
from models.store_model import Store, Tag
from db.base import Base
from db.session import engine

def seed_data():
    db = SessionLocal()
    
    try:
        # 태그 생성
        tag_tteokbokki = Tag(name="떡볶이")
        tag_gimbap = Tag(name="김밥")
        db.add(tag_tteokbokki)
        db.add(tag_gimbap)
        db.commit()
        
        # 매장 생성 (대구 동성로 인근 좌표 - 반경 1km 테스트 용도)
        store1 = Store(name="신참떡볶이 중앙로점", latitude=35.871, longitude=128.593)
        store2 = Store(name="중앙떡볶이 본점", latitude=35.869, longitude=128.594)
        store3 = Store(name="바르다김선생 반월당점", latitude=35.868, longitude=128.591)
        
        # 태그 매핑
        store1.tags.append(tag_tteokbokki)
        store2.tags.append(tag_tteokbokki)
        store3.tags.append(tag_gimbap)
        
        db.add(store1)
        db.add(store2)
        db.add(store3)
        db.commit()
        
        print("✅ Mock data (Stores, Tags) successfully created!")
    except Exception as e:
        print(f"Failed to seed data (Already exists?): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
