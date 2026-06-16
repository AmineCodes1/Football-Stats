import logging
import time
from pymongo import UpdateOne
from db.collections import get_collection
from ingestion.base import paginate, api_get
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logger = logging.getLogger(__name__)


FREE_PLAN_PAGE_LIMIT = 3


def fetch_players(
    league_id: int = DEFAULT_LEAGUE_ID,
    season: int = DEFAULT_SEASON,
) -> int:
    players = paginate("players", {"league": league_id, "season": season}, max_pages=FREE_PLAN_PAGE_LIMIT)
    if not players:
        logger.info("No players returned for league=%s season=%s", league_id, season)
        return 0

    collection = get_collection("players")
    ops = [
        UpdateOne(
            {
                "player.id": p["player"]["id"],
                "statistics.0.league.season": season,
            },
            {"$set": p},
            upsert=True,
        )
        for p in players
    ]
    result = collection.bulk_write(ops, ordered=False)
    logger.info(
        "Players upserted=%d modified=%d for league=%s season=%s",
        result.upserted_count,
        result.modified_count,
        league_id,
        season,
    )
    return result.upserted_count + result.modified_count


def fetch_top_scorers(league_id: int = DEFAULT_LEAGUE_ID, season: int = DEFAULT_SEASON) -> int:
    data = api_get("players/topscorers", {"league": league_id, "season": season})
    players = data.get("response", [])
    if not players:
        return 0

    collection = get_collection("top_scorers")
    ops = [
        UpdateOne(
            {"player.id": p["player"]["id"], "season": season},
            {"$set": {**p, "season": season, "league_id": league_id}},
            upsert=True,
        )
        for p in players
    ]
    result = collection.bulk_write(ops, ordered=False)
    logger.info("Top scorers synced: %d", result.upserted_count + result.modified_count)
    return result.upserted_count + result.modified_count


def fetch_top_assistants(league_id: int = DEFAULT_LEAGUE_ID, season: int = DEFAULT_SEASON) -> int:
    data = api_get("players/topassists", {"league": league_id, "season": season})
    players = data.get("response", [])
    if not players:
        return 0

    collection = get_collection("top_assists")
    ops = [
        UpdateOne(
            {"player.id": p["player"]["id"], "season": season},
            {"$set": {**p, "season": season, "league_id": league_id}},
            upsert=True,
        )
        for p in players
    ]
    result = collection.bulk_write(ops, ordered=False)
    logger.info("Top assists synced: %d", result.upserted_count + result.modified_count)
    return result.upserted_count + result.modified_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_players()
