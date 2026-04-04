from sqlalchemy import String, Integer, Float, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

# 다대다(N:M) 연관 테이블 (매장 1개 - 태그 N개)
store_tag_association = Table(
    "store_tag_association",
    Base.metadata,
    Column("store_id", Integer, ForeignKey("stores.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)

class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    # Store에서 Tag 조회, Tag에서 Store 조회가 모두 가능하도록 설정
    stores = relationship("Store", secondary=store_tag_association, back_populates="tags")


class Store(Base):
    """
    VLM 클러스터링 파이프라인(Tagging)으로부터 생성된 매장 정보를 담는 테이블.
    채팅 앱에서는 GPS(위, 경도)를 기준으로 이 테이블에서 주변 매장을 검색.
    """
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Haversine 계산용 좌표
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    tags = relationship("Tag", secondary=store_tag_association, back_populates="stores")
