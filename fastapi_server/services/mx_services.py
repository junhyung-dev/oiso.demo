from core.config import settings
from sqlalchemy.orm import Session
from typing import Tuple

#커스텀 예외
from exceptions.http import NotFoundException
from sqlalchemy import select, and_
from models.mx_model import ClusterArray
from schemas.mx_schema import MarkerItem, PostItem



def parse_latlng(value: str) -> Tuple[float,float]:
    """
    lat,lng 형식의 str받아서 (lat, lng) 튜플로 반환

    예:
        "35.889,128.612" -> (35.889, 128.612)
    """
    parts = value.split(",")

    lat = float(parts[0].strip())
    lng = float(parts[1].strip())

    #예외 처리는 나중에

    return lat, lng


def get_clusters_in_bbox(db: Session, min_lng: float, max_lng: float, min_lat: float, max_lat: float):
    """
    Bounding Box 범위 내의 클러스터를 모두 가져오는 쿼리
    """
    stmt = select(ClusterArray).where(
        and_(
            ClusterArray.latitude >= min_lat,
            ClusterArray.latitude <= max_lat,
            ClusterArray.longitude >= min_lng,
            ClusterArray.longitude <= max_lng
        )
    )

    clusters = db.execute(stmt).scalars().all()
    return clusters


def get_closest_cluster(db: Session, user_lat: float, user_lng: float):
    """
    Nearmode = False일때, 사용자에 가까운 cluster를 1개 가져옴
    """
    # 유저 위치(user_lat, user_long)와 가장 가까운 클러스터 1개 가져오기

    lat_diff = ClusterArray.latitude - user_lat
    lng_diff = ClusterArray.longitude - user_lng

    distance_expr = lat_diff * lat_diff + lng_diff * lng_diff

    stmt = select(ClusterArray).order_by(distance_expr)
    closest_cluster = db.execute(stmt).scalars().first()

    return closest_cluster

def get_cluster_by_no(db: Session, cluster_no: int):
    """
    cluster_no로 cluster 정보를 가져옴
    """
    cluster = db.get(ClusterArray, cluster_no)
    return cluster


def get_markers(db: Session, user_lng: float, user_lat: float, screen_topleft: str, screen_bottomright: str, nearmode: bool) -> str:
    """
    이미지를 S3(MinIO)에 업로드하고 URL 반환
    """

    # screen_topleft, screen_bottomright 파싱 -> bounding box
    max_lat, min_lng = parse_latlng(screen_topleft)
    min_lat, max_lng = parse_latlng(screen_bottomright)

    #DB에서 latitude ->  min_lat ~ max_lat, longitude -> min_lng ~ max_lng 사이에 있는거 뽑아내기
    clusters = get_clusters_in_bbox(db, min_lng,max_lng,min_lat,max_lat)

    # nearmode 분기 
    if not clusters:
        # (nearmode=False -> user_lat, user_long 이용해서 가장 가까운 클러스터)
        if nearmode == False:
            #추후 postGIS쓰면 편할듯?
            closest = get_closest_cluster(db, user_lat, user_lng)
            clusters = [closest] if closest else []

        else:
            clusters = []

            
    markers = []
    
    #가져온 cluster들을 for문 돌면서 marker로 조립
    for cluster in clusters:

        string_tags = [tag.tagstring for tag in cluster.tags]

        #URL은 아직 더미로
        dummy_url = "http://dummy.com/dummy.jpg"

        marker = MarkerItem(
            longitude=str(cluster.longitude),
            latitude=str(cluster.latitude),
            cluster_no=cluster.clusterno,
            cluster_tags=string_tags,
            cluster_pics_lowres_url=dummy_url,
        )


        markers.append(marker)
    
    return markers


def get_markers_infos(db: Session, cluster_no: int) -> str:
    """
    각 마커에 대한 세부 정보를 볼 수 있도록 한다.
    """

    # cluster 가져오기
    cluster = get_cluster_by_no(db, cluster_no)

    # cluster가 없다면
    if not cluster:
        raise NotFoundException(reason=f"cluster_no:{cluster_no}에 대한 정보가 없습니다.")
    
    # 있으면 response body조립
    posts = []
    # 클러스터에 연결된 사진들을 통해 PostItem 조립
    for picture in cluster.pictures:
        tags = [tag.tagstring for tag in picture.tags]
        dummy_highres_url = f"http://dummy.com/{picture.pic_name}"

        post = PostItem(
            image_no=picture.uniqueid,
            image_tags=tags,
            pic_highres_url=dummy_highres_url
        )
        posts.append(post)

    return posts
        
