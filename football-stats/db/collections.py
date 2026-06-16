from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from db.connection import get_db
import logging

logger = logging.getLogger(__name__)


def get_collection(name: str) -> Collection:
    return get_db()[name]


def setup_indexes() -> None:
    db = get_db()

    db["matches"].create_index([("fixture.id", ASCENDING)], unique=True)
    db["matches"].create_index([("league.id", ASCENDING)])
    db["matches"].create_index([("fixture.date", DESCENDING)])
    db["matches"].create_index([("teams.home.id", ASCENDING)])
    db["matches"].create_index([("teams.away.id", ASCENDING)])

    db["players"].create_index(
        [("player.id", ASCENDING), ("statistics.0.league.season", ASCENDING)],
        unique=True,
    )
    db["players"].create_index([("statistics.0.league.id", ASCENDING)])
    db["players"].create_index([("statistics.0.team.id", ASCENDING)])

    db["teams"].create_index([("team.id", ASCENDING)], unique=True)
    db["teams"].create_index([("league.id", ASCENDING)])

    db["standings"].create_index(
        [("league.id", ASCENDING), ("league.season", ASCENDING)], unique=True
    )

    db["processed_matches"].create_index([("fixture_id", ASCENDING)], unique=True)
    db["processed_players"].create_index(
        [("player_id", ASCENDING), ("season", ASCENDING)], unique=True
    )
    db["processed_teams"].create_index(
        [("team_id", ASCENDING), ("season", ASCENDING)], unique=True
    )

    logger.info("All MongoDB indexes created")
