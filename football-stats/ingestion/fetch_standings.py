import logging
from pymongo import UpdateOne
from db.collections import get_collection
from ingestion.base import api_get
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logger = logging.getLogger(__name__)


def fetch_standings(
    league_id: int = DEFAULT_LEAGUE_ID,
    season: int = DEFAULT_SEASON,
) -> int:
    data = api_get("standings", {"league": league_id, "season": season})
    leagues = data.get("response", [])
    if not leagues:
        logger.info("No standings returned for league=%s season=%s", league_id, season)
        return 0

    collection = get_collection("standings")
    ops = [
        UpdateOne(
            {"league.id": league_id, "league.season": season},
            {"$set": entry},
            upsert=True,
        )
        for entry in leagues
    ]
    result = collection.bulk_write(ops, ordered=False)
    logger.info(
        "Standings upserted=%d modified=%d for league=%s season=%s",
        result.upserted_count,
        result.modified_count,
        league_id,
        season,
    )
    return result.upserted_count + result.modified_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_standings()
