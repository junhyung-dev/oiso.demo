"""
Seed 스크립트: 새 CSV 파일 → DB warm start

사용법:
    python seed_mx_data.py
    python seed_mx_data.py --data-dir ./data
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from db.session import get_db
from models.mx_model import (
    ClusterArray,
    Image,
    Metadata,
    PerPicTags,
    Picture,
    PictureList,
    Tag,
    TagList,
)


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def read_single_column(path: Path, column: str) -> list[str]:
    """헤더가 있는 단일 컬럼 CSV 읽기"""
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [row[column].strip() for row in reader if row.get(column, "").strip()]


def reset_all_tables(db) -> None:
    """FK 의존성 순서에 맞춰 전체 삭제"""
    db.query(TagList).delete()
    db.query(PerPicTags).delete()
    db.query(PictureList).delete()
    db.query(Picture).delete()
    db.query(Image).delete()
    db.query(Metadata).delete()
    db.query(ClusterArray).delete()
    db.query(Tag).delete()
    db.commit()


def seed_mx_data(data_dir: Path) -> None:
    # ─── CSV 파일 경로 ───────────────────────────────────────
    tag_path = data_dir / "tag.csv"
    cluster_path = data_dir / "cluster_array.csv"
    image_path = data_dir / "image.csv"
    metadata_path = data_dir / "metadata.csv"
    picture_path = data_dir / "picture.csv"
    per_pic_tags_path = data_dir / "per_pic_tags.csv"
    picture_list_path = data_dir / "picture_list.csv"
    tag_list_path = data_dir / "tag_list.csv"

    # ─── CSV 읽기 ────────────────────────────────────────────
    tag_names = read_single_column(tag_path, "tag_string")
    clusters = read_csv_rows(cluster_path)
    images = read_csv_rows(image_path)
    metadata_rows = read_csv_rows(metadata_path)
    pictures = read_csv_rows(picture_path)
    per_pic_tags = read_csv_rows(per_pic_tags_path)
    picture_list = read_csv_rows(picture_list_path)
    tag_list = read_csv_rows(tag_list_path)

    db = next(get_db())
    try:
        reset_all_tables(db)

        # 1) Tag
        db.add_all(
            Tag(tag_string=name)
            for name in sorted(set(tag_names))
        )
        db.flush()
        print(f"  tags: {len(set(tag_names))}")

        # 2) ClusterArray
        db.add_all(
            ClusterArray(
                cluster_no=int(row["cluster_no"]),
                longitude=float(row["centric_point_long"]),
                latitude=float(row["centric_point_lat"]),
            )
            for row in clusters
        )
        db.flush()
        print(f"  clusters: {len(clusters)}")

        # 3) Image
        db.add_all(
            Image(
                unique_id=row["unique_id"],
                s3_bucket=row["s3_bucket"] or None,
                s3_key=row["s3_key"] or None,
                s3_version=row["s3_version"] or None,
            )
            for row in images
        )
        db.flush()
        print(f"  images: {len(images)}")

        # 4) Metadata
        db.add_all(
            Metadata(
                unique_id=row["unique_id"],
                longitude=float(row["longitude"]) if row["longitude"] else None,
                latitude=float(row["latitude"]) if row["latitude"] else None,
                time_stamp=row["time_stamp"] or None,
            )
            for row in metadata_rows
        )
        db.flush()
        print(f"  metadata: {len(metadata_rows)}")

        # 5) Picture
        db.add_all(
            Picture(
                unique_id=row["unique_id"],
                created_date=row["created_date"] or None,
                image_id=row["image_id"] or None,
                metadata_id=row["metadata_id"] or None,
            )
            for row in pictures
        )
        db.flush()
        print(f"  pictures: {len(pictures)}")

        # 6) PictureList (cluster ↔ picture)
        db.add_all(
            PictureList(
                cluster_no=int(row["cluster_no"]),
                pic_no=row["pic_no"],
            )
            for row in picture_list
        )
        db.flush()
        print(f"  picture_list: {len(picture_list)}")

        # 7) PerPicTags (picture ↔ tag)
        seen: set[tuple[str, str]] = set()
        pic_tags = []
        for row in per_pic_tags:
            uid = row["unique_id"]
            tag = row["tag"]
            if not tag:
                continue
            key = (uid, tag)
            if key in seen:
                continue
            seen.add(key)
            pic_tags.append(PerPicTags(unique_id=uid, tag=tag))

        db.add_all(pic_tags)
        db.flush()
        print(f"  per_pic_tags: {len(pic_tags)}")

        # 8) TagList (cluster ↔ tag)
        seen_ct: set[tuple[int, str]] = set()
        cluster_tags = []
        for row in tag_list:
            cno = int(row["cluster_no"])
            tag = row["tag"]
            if not tag:
                continue
            key = (cno, tag)
            if key in seen_ct:
                continue
            seen_ct.add(key)
            cluster_tags.append(TagList(cluster_no=cno, tag=tag))

        db.add_all(cluster_tags)
        db.commit()
        print(f"  tag_list: {len(cluster_tags)}")

        print("\nSeed completed successfully!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed map data from CSV files.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing the new CSV files.",
    )
    args = parser.parse_args()

    seed_mx_data(args.data_dir)


if __name__ == "__main__":
    main()
