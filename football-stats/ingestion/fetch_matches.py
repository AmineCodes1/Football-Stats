import logging
from datetime import datetime, timedelta
from pymongo import UpdateOne
from db.collections import get_collection
from ingestion.base import paginate
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logger = logging.getLogger(__name__)


def fetch_matches(
    league_id: int = DEFAULT_LEAGUE_ID,
    season: int = DEFAULT_SEASON,
    from_date: str | None = None,
    to_date: str | None = None,
) -> int:
    params: dict = {"league": league_id, "season": season}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    fixtures = paginate("fixtures", params)
    if not fixtures:
        logger.info("No fixtures returned for league=%s season=%s", league_id, season)
        return 0

    collection = get_collection("matches")
    ops = [
        UpdateOne(
            {"fixture.id": f["fixture"]["id"]},
            {"$set": f},
            upsert=True,
        )
        for f in fixtures
    ]
    result = collection.bulk_write(ops, ordered=False)
    count = result.upserted_count + result.modified_count
    logger.info(
        "Matches upserted=%d modified=%d for league=%s season=%s",
        result.upserted_count,
        result.modified_count,
        league_id,
        season,
    )
    return count


def fetch_recent_matches(days: int = 7, league_id: int = DEFAULT_LEAGUE_ID, season: int = DEFAULT_SEASON) -> int:
    today = datetime.utcnow()
    from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    return fetch_matches(league_id, season, from_date, to_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_matches()
