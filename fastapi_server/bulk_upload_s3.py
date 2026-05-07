"""
벌크 업로드 스크립트: 로컬 사진 파일 → S3 업로드

CSV 매핑 체인:
  pics.csv (pic_no → pic_name)
  pic_no_mapping.csv (pic_no → picture_unique_id)
  picture.csv (picture_unique_id → image_id)
  image.csv (image_id → s3_key, s3_bucket)

사용법:
    python bulk_upload_s3.py
    python bulk_upload_s3.py --photo-dir ./data/result --dry-run
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from core.storage import get_s3_client, get_bucket_name


DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_PHOTO_DIR = DATA_DIR / "result"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_pic_name_to_s3key(data_dir: Path) -> dict[str, tuple[str, str]]:
    """
    원본 pic_name → (s3_bucket, s3_key) 매핑을 구축합니다.

    체인: pics.csv → pic_no_mapping.csv → picture.csv → image.csv
    """
    # 1) pic_no → pic_name
    pics = read_csv_rows(data_dir / "pics.csv")
    pic_no_to_name: dict[str, str] = {
        row["pic_no"]: row["pic_name"] for row in pics
    }

    # 2) pic_no → picture_unique_id
    mappings = read_csv_rows(data_dir / "pic_no_mapping.csv")
    pic_no_to_pid: dict[str, str] = {
        row["pic_no"]: row["picture_unique_id"] for row in mappings
    }

    # 3) picture_unique_id → image_id
    pictures = read_csv_rows(data_dir / "picture.csv")
    pid_to_image_id: dict[str, str] = {
        row["unique_id"]: row["image_id"] for row in pictures
    }

    # 4) image_id → (s3_bucket, s3_key)
    images = read_csv_rows(data_dir / "image.csv")
    image_id_to_s3: dict[str, tuple[str, str]] = {
        row["unique_id"]: (row["s3_bucket"], row["s3_key"])
        for row in images
    }

    # 체인 조합: pic_name → (s3_bucket, s3_key)
    result: dict[str, tuple[str, str]] = {}
    for pic_no, pic_name in pic_no_to_name.items():
        pid = pic_no_to_pid.get(pic_no)
        if not pid:
            continue
        image_id = pid_to_image_id.get(pid)
        if not image_id:
            continue
        s3_info = image_id_to_s3.get(image_id)
        if not s3_info:
            continue
        result[pic_name] = s3_info

    return result


def resolve_local_file(photo_dir: Path, pic_name: str) -> Path | None:
    """
    로컬 사진 파일 경로를 찾습니다.
    원본이 .heic인 경우, .jpg로 변환된 파일을 찾습니다.
    """
    # 원본 파일명으로 먼저 시도
    candidate = photo_dir / pic_name
    if candidate.exists():
        return candidate

    # .heic → .jpg 변환 시도 (result 폴더에는 jpg만 있으므로)
    stem = Path(pic_name).stem
    jpg_candidate = photo_dir / f"{stem}.jpg"
    if jpg_candidate.exists():
        return jpg_candidate

    return None


def bulk_upload(photo_dir: Path, data_dir: Path, dry_run: bool = False) -> None:
    mapping = build_pic_name_to_s3key(data_dir)
    print(f"Mapped {len(mapping)} pictures to S3 keys")

    if not dry_run:
        s3_client = get_s3_client()

    # 환경에 맞는 버킷명 사용 (로컬=MinIO, EC2=S3)
    bucket = get_bucket_name()
    print(f"Target bucket: {bucket}")

    uploaded = 0
    skipped = 0
    not_found = 0

    for pic_name, (_, s3_key) in sorted(mapping.items()):
        local_file = resolve_local_file(photo_dir, pic_name)

        if local_file is None:
            print(f"  [SKIP] {pic_name} -> file not found")
            not_found += 1
            continue

        if dry_run:
            print(f"  [DRY] {local_file.name} -> s3://{bucket}/{s3_key}")
            uploaded += 1
            continue

        try:
            # Content-Type 설정
            content_type = "image/jpeg"
            if s3_key.endswith(".heic"):
                content_type = "image/heic"
            elif s3_key.endswith(".png"):
                content_type = "image/png"

            s3_client.upload_file(
                str(local_file),
                bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )
            uploaded += 1

            if uploaded % 50 == 0:
                print(f"  ... uploaded {uploaded} files")

        except Exception as e:
            print(f"  [ERROR] {pic_name}: {e}")
            skipped += 1

    print(f"\nDone! uploaded={uploaded}, not_found={not_found}, errors={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk upload photos to S3")
    parser.add_argument(
        "--photo-dir",
        type=Path,
        default=DEFAULT_PHOTO_DIR,
        help="Directory containing the photo files",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Directory containing CSV mapping files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without actually uploading",
    )
    args = parser.parse_args()

    bulk_upload(args.photo_dir, args.data_dir, args.dry_run)


if __name__ == "__main__":
    main()
