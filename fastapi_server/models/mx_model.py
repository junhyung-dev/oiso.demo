from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Tag(Base):
    __tablename__ = "tags"

    tagstring: Mapped[str] = mapped_column(String(100), primary_key=True)

    #태그 하나는 여러 사진에 붙을 수 있다. 중간연결 테이블 - picture_tags
    pictures: Mapped[List["Picture"]] = relationship(
        secondary="picture_tags",
        back_populates="tags",
    )

    clusters: Mapped[List["ClusterArray"]] = relationship(
        secondary="cluster_tags",
        back_populates="tags",
    )


class ClusterArray(Base):
    __tablename__ = "cluster_array"

    clusterno: Mapped[int] = mapped_column(Integer, primary_key=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)

    #클러스터 하나에는 여러 사진이 붙을 수 있다.
    pictures: Mapped[List["Picture"]] = relationship(
        secondary="cluster_pictures",
        back_populates="clusters",
    )

    tags: Mapped[List["Tag"]] = relationship(
        secondary="cluster_tags",
        back_populates="clusters",
    )


class Metadata(Base):
    __tablename__ = "metadata"

    uniqueid: Mapped[int] = mapped_column(Integer, primary_key=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # uselist=False: 1대1 느낌
    picture: Mapped[Optional["Picture"]] = relationship(
        back_populates="pic_metadata",
        uselist=False,
    )


class Picture(Base):
    __tablename__ = "picture"

    uniqueid: Mapped[int] = mapped_column(Integer, primary_key=True)
    pic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    serving_pic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("metadata.uniqueid"),
        nullable=True,
    )

    # 사진에서 메타데이터 접근가능 - picture.pic_metadata.longitude 같이
    pic_metadata: Mapped[Optional["Metadata"]] = relationship(back_populates="picture")

    # 사진이 어떤 클러스터에 속하는지
    clusters: Mapped[List["ClusterArray"]] = relationship(
        secondary="cluster_pictures",
        back_populates="pictures",
    )
    # 사진에 붙은 태그목록
    tags: Mapped[List["Tag"]] = relationship(
        secondary="picture_tags",
        back_populates="pictures",
    )


class ClusterPicture(Base):
    __tablename__ = "cluster_pictures"

    cluster_no: Mapped[int] = mapped_column(
        ForeignKey("cluster_array.clusterno"),
        primary_key=True,
    )
    pic_no: Mapped[int] = mapped_column(
        ForeignKey("picture.uniqueid"),
        primary_key=True,
    )


class PictureTag(Base):
    __tablename__ = "picture_tags"

    pic_no: Mapped[int] = mapped_column(
        ForeignKey("picture.uniqueid"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        ForeignKey("tags.tagstring"),
        primary_key=True,
    )

class ClusterTag(Base):
    __tablename__ = "cluster_tags"

    cluster_no: Mapped[int] = mapped_column(
        ForeignKey("cluster_array.clusterno"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(
        ForeignKey("tags.tagstring"),
        primary_key=True,
    )
