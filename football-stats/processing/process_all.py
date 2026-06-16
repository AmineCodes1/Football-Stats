"""
Run all processing transformations and save results to MongoDB processed_* collections.

Usage:
    python processing/process_all.py
    python processing/process_all.py --league 140 --season 2024
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing.clean_matches import load_matches_df, compute_form_table, save_processed_matches
from processing.clean_players import load_players_df, compute_player_rankings, save_processed_players
from processing.stats import compute_team_stats, compute_league_summary, save_league_summary, compute_top_scorers, save_top_scorers, compute_top_assists, save_top_assists
from db.collections import get_collection
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_all(league_id: int, season: int) -> None:
    logger.info("=== Processing pipeline start: league=%s season=%s ===", league_id, season)

    logger.info("--- Processing matches ---")
    matches_df = load_matches_df(league_id, season)
    if not matches_df.empty:
        save_processed_matches(matches_df)

        logger.info("--- Computing team stats ---")
        team_stats = compute_team_stats(matches_df)
        team_records = team_stats.to_dict("records")
        ts_col = get_collection("processed_teams")
        for rec in team_records:
            rec["league_id"] = league_id
            rec["season"] = season
            ts_col.update_one(
                {"team_id": rec["team_id"], "season": season},
                {"$set": rec},
                upsert=True,
            )
        logger.info("Saved %d team stat records", len(team_records))

        logger.info("--- Computing form table ---")
        form_df = compute_form_table(matches_df)
        form_records = form_df.to_dict("records")
        form_col = get_collection("processed_form")
        for rec in form_records:
            rec["league_id"] = league_id
            rec["season"] = season
            form_col.update_one(
                {"team_id": rec["team_id"], "season": season},
                {"$set": rec},
                upsert=True,
            )
        logger.info("Saved %d form records", len(form_records))
    else:
        logger.warning("No match data found for league=%s season=%s", league_id, season)

    logger.info("--- Processing players ---")
    players_df = load_players_df(league_id, season)
    if not players_df.empty:
        ranked = compute_player_rankings(players_df)
        save_processed_players(ranked)
    else:
        logger.warning("No player data found for league=%s season=%s", league_id, season)

    logger.info("--- Computing league summary ---")
    summary = compute_league_summary(league_id, season)
    save_league_summary(summary)

    logger.info("--- Computing top scorers ---")
    top_scorers = compute_top_scorers(league_id, season, limit=20)
    save_top_scorers(top_scorers)

    logger.info("--- Computing top assists ---")
    top_assists = compute_top_assists(league_id, season, limit=20)
    save_top_assists(top_assists)

    logger.info("=== Processing pipeline complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all processing transformations")
    parser.add_argument("--league", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=DEFAULT_SEASON)
    args = parser.parse_args()
    run_all(args.league, args.season)
