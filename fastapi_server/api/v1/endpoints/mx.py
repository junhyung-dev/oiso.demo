from fastapi import APIRouter, Query
from typing import Optional

from schemas.mx_schema import (
    GetMarkersResponse,
    MarkerItem,
    MarkerInfosResponse,
    PostItem,
)

router = APIRouter()


@router.get("/get_markers", response_model=GetMarkersResponse)
async def get_markers(
    user_long: float = Query(..., description="유저 현재 경도"),
    user_lat: float = Query(..., description="유저 현재 위도"),
    screen_topleft: str = Query(..., description="화면 좌상단 위경도 (예: '35.9,128.5')"),
    screen_topright: str = Query(..., description="화면 우하단 위경도 (예: '35.8,128.6')"),
    nearmode: bool = Query(True, description="True: 범위 내 없으면 빈 배열 / False: 가장 가까운 것 반환"),
):
    """
    현재 지도 화면 범위 내의 클러스터 마커 목록을 반환합니다.

    - 현재: 더미 마커 1개 반환
    - 추후: PostgreSQL ClusterArray/TagList 조회 + MinIO lowres 이미지 URL 반환
    """
    # TODO: bounding box 파싱 → ClusterArray/TagList DB 조회 → MinIO URL 반환
    dummy_markers = [
        MarkerItem(
            longitude=str(user_long + 0.001),
            latitude=str(user_lat + 0.001),
            cluster_no=1,
            cluster_tags=["더미태그1", "더미태그2"],
            cluster_pics_lowres_url="http://localhost:9000/images/dummy_lowres.jpg",
        )
    ]
    return GetMarkersResponse(response="success (dummy)", markers=dummy_markers)


@router.get("/marker_infos", response_model=MarkerInfosResponse)
async def marker_infos(
    cluster_no: int = Query(..., description="조회할 클러스터 번호"),
):
    """
    특정 클러스터 번호에 해당하는 게시물(사진+태그) 목록을 반환합니다.

    - 현재: 더미 게시물 1개 반환
    - 추후: ClusterArray → TagList → Picture 조회 + MinIO highres 이미지 URL 반환
    """
    # TODO: ClusterArray 조회 → Picture 목록 → MinIO highres URL 반환
    dummy_posts = [
        PostItem(
            image_no=1,
            image_tags=["더미태그1", "더미태그2"],
            pic_highres_url="http://localhost:9000/images/dummy_highres.jpg",
        )
    ]
    return MarkerInfosResponse(response="success (dummy)", posts=dummy_posts)
