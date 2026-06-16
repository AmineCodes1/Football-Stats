"""
Manual entry point: fetch all data from API-Football and store in MongoDB.

Usage:
    python ingestion/fetch_all.py
    python ingestion/fetch_all.py --league 140 --season 2024
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.collections import setup_indexes
from ingestion.fetch_matches import fetch_matches
from ingestion.fetch_players import fetch_players, fetch_top_scorers, fetch_top_assistants
from ingestion.fetch_teams import fetch_teams
from ingestion.fetch_standings import fetch_standings
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_all(league_id: int, season: int) -> None:
    logger.info("=== Football Stats: Full Data Pull ===")
    logger.info("League: %s  Season: %s", league_id, season)

    logger.info("--- Setting up indexes ---")
    setup_indexes()

    logger.info("--- Fetching standings ---")
    fetch_standings(league_id, season)

    logger.info("--- Fetching teams ---")
    fetch_teams(league_id, season)

    logger.info("--- Fetching matches ---")
    fetch_matches(league_id, season)

    logger.info("--- Fetching players ---")
    fetch_players(league_id, season)

    logger.info("--- Fetching top scorers ---")
    fetch_top_scorers(league_id, season)

    logger.info("--- Fetching top assistants ---")
    fetch_top_assistants(league_id, season)

    logger.info("=== Full data pull complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch all football stats data")
    parser.add_argument("--league", type=int, default=DEFAULT_LEAGUE_ID, help="League ID (default: 39 = Premier League)")
    parser.add_argument("--season", type=int, default=DEFAULT_SEASON, help="Season year (default: 2024)")
    args = parser.parse_args()
    run_all(args.league, args.season)
