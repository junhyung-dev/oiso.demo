import argparse
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from db.session import SessionLocal
from models.mx_model import (
    ClusterArray,
    ClusterPicture,
    ClusterTag,
    Metadata,
    Picture,
    PictureTag,
    Tag,
)


DEFAULT_DATA_DIR = Path.home() / "Downloads" / "DB_FOR_BACK"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def read_tag_names(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return {line.strip() for line in csv_file if line.strip()}


def get_serving_pic_name(pic_name: str) -> str:
    path = Path(pic_name)
    if path.suffix.lower() == ".heic":
        return f"{path.stem}.jpg"
    return pic_name


def reset_mx_tables(db) -> None:
    db.query(ClusterTag).delete()
    db.query(PictureTag).delete()
    db.query(ClusterPicture).delete()
    db.query(Picture).delete()
    db.query(Metadata).delete()
    db.query(ClusterArray).delete()
    db.query(Tag).delete()
    db.commit()


def seed_mx_data(data_dir: Path) -> None:
    groups_path = data_dir / "groups.csv"
    pics_path = data_dir / "pics.csv"
    tags_path = data_dir / "tags.csv"
    all_tags_path = data_dir / "all_tags.csv"

    groups = read_csv_rows(groups_path)
    pics = read_csv_rows(pics_path)
    picture_tag_rows = read_csv_rows(tags_path)

    tag_names = read_tag_names(all_tags_path)
    tag_names.update(row["pic_tag"] for row in picture_tag_rows if row.get("pic_tag"))

    db = SessionLocal()
    try:
        reset_mx_tables(db)

        db.add_all(
            Tag(tagstring=tag_name)
            for tag_name in sorted(tag_names)
        )
        db.flush()

        db.add_all(
            ClusterArray(
                clusterno=int(row["group_no"]),
                longitude=float(row["centric_point_long"]),
                latitude=float(row["centric_point_lat"]),
            )
            for row in groups
        )
        db.flush()

        db.add_all(
            Metadata(
                uniqueid=int(row["pic_no"]),
                longitude=float(row["centric_point_long"]),
                latitude=float(row["centric_point_lat"]),
                timestamp=None,
            )
            for row in pics
        )
        db.flush()

        db.add_all(
            Picture(
                uniqueid=int(row["pic_no"]),
                pic_name=row["pic_name"],
                serving_pic_name=get_serving_pic_name(row["pic_name"]),
                created_date=None,
                metadata_id=int(row["pic_no"]),
            )
            for row in pics
        )
        db.flush()

        db.add_all(
            ClusterPicture(
                cluster_no=int(row["group_no"]),
                pic_no=int(row["pic_no"]),
            )
            for row in pics
        )
        db.flush()

        seen_picture_tags: set[tuple[int, str]] = set()
        picture_tags = []
        for row in picture_tag_rows:
            pic_no = int(row["pic_no"])
            tag = row["pic_tag"]
            if not tag:
                continue
            key = (pic_no, tag)
            if key in seen_picture_tags:
                continue
            seen_picture_tags.add(key)
            picture_tags.append(PictureTag(pic_no=pic_no, tag=tag))

        db.add_all(picture_tags)
        db.flush()

        pic_to_cluster = {
            int(row["pic_no"]): int(row["group_no"])
            for row in pics
        }

        cluster_tag_keys: set[tuple[int, str]] = set()
        for row in picture_tag_rows:
            pic_no = int(row["pic_no"])
            tag = row["pic_tag"]
            if not tag:
                continue
            cluster_no = pic_to_cluster[pic_no]
            cluster_tag_keys.add((cluster_no, tag))

        cluster_tags = [
            ClusterTag(cluster_no=cluster_no, tag=tag)
            for cluster_no, tag in sorted(cluster_tag_keys)
        ]

        db.add_all(cluster_tags)
        db.commit()

        print("MX seed completed.")
        print(f"- tags: {len(tag_names)}")
        print(f"- clusters: {len(groups)}")
        print(f"- pictures: {len(pics)}")
        print(f"- picture_tags: {len(picture_tags)}")
        print(f"- cluster_tags: {len(cluster_tags)}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed mx map data from CSV files.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing groups.csv, pics.csv, tags.csv, and all_tags.csv.",
    )
    args = parser.parse_args()

    seed_mx_data(args.data_dir)


if __name__ == "__main__":
    main()
