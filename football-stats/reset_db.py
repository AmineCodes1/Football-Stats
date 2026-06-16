"""
Clean the football_stats database by dropping all collections.

Usage:
    python reset_db.py              # drops all collections
    python reset_db.py --raw        # drops only raw ingestion collections
    python reset_db.py --processed  # drops only processed collections
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAW_COLLECTIONS = [
    "players",
    "matches",
    "teams",
    "standings",
    "top_scorers",
    "top_assists",
]

PROCESSED_COLLECTIONS = [
    "processed_players",
    "processed_matches",
    "processed_teams",
    "processed_form",
    "processed_top_scorers",
    "processed_top_assists",
    "processed_league_summary",
]


def drop_collections(names: list[str]) -> None:
    db = get_db()
    existing = set(db.list_collection_names())
    for name in names:
        if name in existing:
            db[name].drop()
            logger.info("Dropped collection: %s", name)
        else:
            logger.info("Skipped (not found): %s", name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the football_stats database")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--raw", action="store_true", help="Drop only raw ingestion collections")
    group.add_argument("--processed", action="store_true", help="Drop only processed collections")
    args = parser.parse_args()

    if args.raw:
        logger.info("=== Dropping RAW collections ===")
        drop_collections(RAW_COLLECTIONS)
    elif args.processed:
        logger.info("=== Dropping PROCESSED collections ===")
        drop_collections(PROCESSED_COLLECTIONS)
    else:
        logger.info("=== Dropping ALL collections ===")
        drop_collections(RAW_COLLECTIONS + PROCESSED_COLLECTIONS)

    logger.info("Done.")


if __name__ == "__main__":
    main()
