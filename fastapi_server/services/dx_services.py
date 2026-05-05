from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from core.config import settings
from core.storage import get_s3_client, get_bucket_name


#커스텀 예외
from exceptions.http import BadRequestException, StorageException

from datetime import datetime
from PIL import Image, ExifTags
from PIL.ExifTags import IFD

def _dms_to_decimal(dms: tuple, ref: str) -> float:
    """
    도/분/초(DMS) → 십진수(Decimal Degrees) 변환
    dms: (도, 분, 초) 형태의 튜플
    ref: 'N', 'S', 'E', 'W' 방향값
    """
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600

    # 남위(S), 서경(W)는 음수 처리
    if ref in ("S", "W"):
        decimal = -decimal

    return decimal


def extract_image_metadata(file_obj) -> dict:
    """
    이미지의 메타데이터 추출
    time_stamp, 위도, 경도
    """

    metadata = {
        "longitude" : None,
        "latitude" : None,
        "time_stamp" : None,
    }

    try:
        file_obj.seek(0)
        image = Image.open(file_obj)
        exif = image.getexif()

        if not exif:
            return metadata

        
        # 촬영 시각
        exif_info = exif.get_ifd(IFD.Exif)
        if exif_info and 36867 in exif_info:
            datetime_original = exif_info.get(36867)
            metadata["time_stamp"] = datetime.strptime(
                datetime_original,
                "%Y:%m:%d %H:%M:%S",
            )

        # GPS 정보 -> tag 34853
        if 34853 not in exif:
            return metadata

        gps_info = exif.get_ifd(IFD.GPSInfo)
        if not gps_info:
            return metadata

        # GPS 태그 상수
        # 1=GPSLatitudeRef, 2=GPSLatitude, 3=GPSLongitudeRef, 4=GPSLongitude
        lat_ref = gps_info.get(1)   # 'N' or 'S'
        lat_dms = gps_info.get(2)   # ((도, 1), (분, 1), (초, 100)) 형태
        lon_ref = gps_info.get(3)   # 'E' or 'W'
        lon_dms = gps_info.get(4)

        if lat_ref and lat_dms and lon_ref and lon_dms:
            metadata["latitude"] = _dms_to_decimal(lat_dms, lat_ref)
            metadata["longitude"] = _dms_to_decimal(lon_dms, lon_ref)

        return metadata
        
    except Exception:
        return metadata

    finally:
        file_obj.seek(0)



def build_picture_url(bucket_name: str, s3_key: str) -> str:
    if settings.MINIO_ENDPOINT_URL:
        return f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/{s3_key}"

    # S3 정책에 따라 추후 presigned URL 또는 public URL로 조정
    return f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


def upload_picture(image: UploadFile) -> dict:
    """
    이미지를 S3(MinIO)에 업로드하고 URL 반환
    """

    if not image.filename:
        #이런식으로 Exception던지는게 가능
        raise BadRequestException(reason="업로드할 파일명이 존재하지 않습니다.")

    if not image.content_type or not image.content_type.startswith("image/"):
        raise BadRequestException(reason="이미지 파일만 업로드할 수 있습니다.")
        
    # 고유 파일명 생성
    ext = Path(image.filename).suffix
    s3_key = f"pictures/{uuid4()}{ext}"

    try:
        s3_client = get_s3_client()
        bucket_name = get_bucket_name()


        # 이미지 메타데이터 추출
        metadata = extract_image_metadata(image.file)

        # 이미지 업로드
        s3_client.upload_fileobj(
            image.file,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": image.content_type or "application/octet-stream"},
        )

        s3_version = None
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        # 접근 가능한 URL 생성: {endpoint}/{bucket}/{key}
        picture_url = build_picture_url(bucket_name, s3_key)



        return {
            "picture_url": picture_url,
            "s3_bucket": bucket_name,
            "s3_key": s3_key,
            "s3_version": s3_version,
            "s3_uri": s3_uri,
            "metadata": metadata
        }

    except Exception as e:
        raise StorageException(reason=f"파일 업로드에 실패했습니다. ({str(e)})")
        
