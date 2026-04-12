from pydantic import BaseModel
from typing import List


# ─── /v1/mx/get_markers ─────────────────────────────────────────

class MarkerItem(BaseModel):
    longitude: str
    latitude: str
    cluster_no: int
    cluster_tags: List[str]
    cluster_pics_lowres_url: str  # MinIO URL (lowres 이미지)


class GetMarkersResponse(BaseModel):
    response: str
    markers: List[MarkerItem]


# ─── /v1/mx/marker_infos ─────────────────────────────────────────

class PostItem(BaseModel):
    image_no: int
    image_tags: List[str]
    pic_highres_url: str          # MinIO URL (highres 이미지)


class MarkerInfosResponse(BaseModel):
    response: str
    posts: List[PostItem]
