"""
CSV 변환 스크립트: 기존 warm-start CSV → 최신 DB 스키마 CSV

변환 대상:
  all_tags.csv  → tag.csv                (Tag)
  pics.csv      → picture.csv            (Picture)
                   image.csv              (Image)
                   metadata.csv           (Metadata)
                   picture_list.csv       (PictureList)
  tags.csv      → per_pic_tags.csv       (PerPicTags)
  groups.csv    → cluster_array.csv      (ClusterArray)
                   tag_list.csv           (TagList)
"""

import csv
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# ─── 설정 ────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent

S3_BUCKET = "project1-08-singap-s3"
S3_KEY_PREFIX = "pictures/"      # upload_picture() 에서 사용하는 prefix
CREATED_DATE = datetime.now(
    tz=timezone(timedelta(hours=9))
).strftime("%Y-%m-%d %H:%M:%S")  # warm start → 현재 시각 통일

# ─── 원본 파일 읽기 ──────────────────────────────────────
def read_all_tags(path: Path) -> list[str]:
    """헤더 없는 단일 컬럼 CSV"""
    tags = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            tag = line.strip()
            if tag:
                tags.append(tag)
    return tags


def read_pics(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_groups(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_tags(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ─── 변환 함수 ───────────────────────────────────────────
def generate_s3_key(pic_name: str) -> str:
    """실제 업로드 패턴 pictures/{uuid4()}{ext} 를 모방"""
    ext = Path(pic_name).suffix  # .jpg, .heic 등
    return f"{S3_KEY_PREFIX}{uuid.uuid4()}{ext}"


def convert():
    # 1) 원본 읽기
    all_tags = read_all_tags(DATA_DIR / "all_tags.csv")
    pics = read_pics(DATA_DIR / "pics.csv")
    groups = read_groups(DATA_DIR / "groups.csv")
    tags = read_tags(DATA_DIR / "tags.csv")

    # pic_no → group_no 매핑 (PictureList & TagList 생성용)
    pic_to_group: dict[str, str] = {}
    for p in pics:
        pic_to_group[p["pic_no"]] = p["group_no"]

    # ─────────────────────────────────────────────────────
    # (A) tag.csv  ← all_tags.csv
    # ─────────────────────────────────────────────────────
    out_tag = DATA_DIR / "tag.csv"
    with open(out_tag, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tag_string"])
        for t in all_tags:
            writer.writerow([t])
    print(f"[OK] {out_tag.name}  ({len(all_tags)} rows)")

    # ─────────────────────────────────────────────────────
    # (B) picture.csv / image.csv / metadata.csv  ← pics.csv
    # ─────────────────────────────────────────────────────
    picture_rows = []
    image_rows = []
    metadata_rows = []

    # pic_no → picture_unique_id 매핑 (다른 테이블 FK 참조용)
    pic_no_to_picture_id: dict[str, str] = {}

    for p in pics:
        pic_no = p["pic_no"]
        pic_name = p["pic_name"]
        longitude = p["centric_point_long"]
        latitude = p["centric_point_lat"]

        picture_id = str(uuid.uuid4())
        image_id = str(uuid.uuid4())
        metadata_id = str(uuid.uuid4())

        pic_no_to_picture_id[pic_no] = picture_id

        picture_rows.append({
            "unique_id": picture_id,
            "created_date": CREATED_DATE,
            "image_id": image_id,
            "metadata_id": metadata_id,
        })

        s3_key = generate_s3_key(pic_name)
        image_rows.append({
            "unique_id": image_id,
            "s3_bucket": S3_BUCKET,
            "s3_key": s3_key,
            "s3_version": "",  # 아직 미정 → NULL
        })

        metadata_rows.append({
            "unique_id": metadata_id,
            "longitude": longitude,
            "latitude": latitude,
            "time_stamp": CREATED_DATE,  # warm start: 현재 시각
        })

    # picture.csv
    out_picture = DATA_DIR / "picture.csv"
    with open(out_picture, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["unique_id", "created_date", "image_id", "metadata_id"])
        writer.writeheader()
        writer.writerows(picture_rows)
    print(f"[OK] {out_picture.name}  ({len(picture_rows)} rows)")

    # image.csv
    out_image = DATA_DIR / "image.csv"
    with open(out_image, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["unique_id", "s3_bucket", "s3_key", "s3_version"])
        writer.writeheader()
        writer.writerows(image_rows)
    print(f"[OK] {out_image.name}  ({len(image_rows)} rows)")

    # metadata.csv
    out_metadata = DATA_DIR / "metadata.csv"
    with open(out_metadata, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["unique_id", "longitude", "latitude", "time_stamp"])
        writer.writeheader()
        writer.writerows(metadata_rows)
    print(f"[OK] {out_metadata.name}  ({len(metadata_rows)} rows)")

    # ─────────────────────────────────────────────────────
    # (C) per_pic_tags.csv  ← tags.csv
    # ─────────────────────────────────────────────────────
    out_per_pic_tags = DATA_DIR / "per_pic_tags.csv"
    skipped = 0
    with open(out_per_pic_tags, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["unique_id", "tag"])
        for t in tags:
            pic_no = t["pic_no"]
            picture_id = pic_no_to_picture_id.get(pic_no)
            if picture_id is None:
                skipped += 1
                continue
            writer.writerow([picture_id, t["pic_tag"]])
    print(f"[OK] {out_per_pic_tags.name}  ({len(tags) - skipped} rows, skipped {skipped})")

    # ─────────────────────────────────────────────────────
    # (D) cluster_array.csv  ← groups.csv
    # ─────────────────────────────────────────────────────
    out_cluster = DATA_DIR / "cluster_array.csv"
    with open(out_cluster, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster_no", "centric_point_long", "centric_point_lat"])
        for g in groups:
            writer.writerow([
                g["group_no"],
                g["centric_point_long"],
                g["centric_point_lat"],
            ])
    print(f"[OK] {out_cluster.name}  ({len(groups)} rows)")

    # ─────────────────────────────────────────────────────
    # (E) picture_list.csv  ← pics.csv (cluster ↔ picture 매핑)
    # ─────────────────────────────────────────────────────
    out_pic_list = DATA_DIR / "picture_list.csv"
    with open(out_pic_list, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster_no", "pic_no"])
        for p in pics:
            picture_id = pic_no_to_picture_id[p["pic_no"]]
            writer.writerow([p["group_no"], picture_id])
    print(f"[OK] {out_pic_list.name}  ({len(pics)} rows)")

    # ─────────────────────────────────────────────────────
    # (F) tag_list.csv  ← tags.csv + pics.csv 파생
    #     클러스터별 고유 태그 목록
    # ─────────────────────────────────────────────────────
    cluster_tags: dict[str, set[str]] = defaultdict(set)
    for t in tags:
        pic_no = t["pic_no"]
        group_no = pic_to_group.get(pic_no)
        if group_no is not None:
            cluster_tags[group_no].add(t["pic_tag"])

    out_tag_list = DATA_DIR / "tag_list.csv"
    row_count = 0
    with open(out_tag_list, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster_no", "tag"])
        for cluster_no in sorted(cluster_tags.keys(), key=int):
            for tag in sorted(cluster_tags[cluster_no]):
                writer.writerow([cluster_no, tag])
                row_count += 1
    print(f"[OK] {out_tag_list.name}  ({row_count} rows)")

    # ─────────────────────────────────────────────────────
    # (G) pic_no → picture_id 매핑 저장 (디버깅 / 참조용)
    # ─────────────────────────────────────────────────────
    out_mapping = DATA_DIR / "pic_no_mapping.csv"
    with open(out_mapping, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pic_no", "picture_unique_id"])
        for pic_no, pid in sorted(pic_no_to_picture_id.items(), key=lambda x: int(x[0])):
            writer.writerow([pic_no, pid])
    print(f"[OK] {out_mapping.name}  ({len(pic_no_to_picture_id)} rows)  [참조용]")

    print(f"\n변환 완료! 출력 디렉토리: {DATA_DIR}")


if __name__ == "__main__":
    convert()
