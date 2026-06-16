import logging
import pandas as pd
from db.collections import get_collection

logger = logging.getLogger(__name__)


def load_players_df(league_id: int | None = None, season: int | None = None) -> pd.DataFrame:
    query: dict = {}
    if league_id:
        query["statistics.0.league.id"] = league_id
    if season:
        query["statistics.0.league.season"] = season

    raw = list(get_collection("players").find(query, {"_id": 0}))
    if not raw:
        return pd.DataFrame()

    rows = []
    for doc in raw:
        player = doc.get("player", {})
        for stat in doc.get("statistics", []):
            team = stat.get("team", {})
            league = stat.get("league", {})
            games = stat.get("games", {})
            goals = stat.get("goals", {})
            passes = stat.get("passes", {})
            tackles = stat.get("tackles", {})
            dribbles = stat.get("dribbles", {})
            shots = stat.get("shots", {})
            cards = stat.get("cards", {})

            rows.append({
                "player_id": player.get("id"),
                "player_name": player.get("name"),
                "nationality": player.get("nationality"),
                "age": player.get("age"),
                "position": games.get("position"),
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "league_id": league.get("id"),
                "league_name": league.get("name"),
                "season": league.get("season"),
                "appearances": games.get("appearences"),
                "minutes_played": games.get("minutes"),
                "goals": goals.get("total") or 0,
                "assists": goals.get("assists") or 0,
                "shots_total": shots.get("total") or 0,
                "shots_on_target": shots.get("on") or 0,
                "passes_total": passes.get("total") or 0,
                "passes_accuracy": passes.get("accuracy"),
                "tackles_total": tackles.get("total") or 0,
                "dribbles_success": dribbles.get("success") or 0,
                "yellow_cards": cards.get("yellow") or 0,
                "red_cards": cards.get("red") or 0,
            })

    df = pd.DataFrame(rows)
    return df


def compute_player_rankings(df: pd.DataFrame, min_appearances: int = 1) -> pd.DataFrame:
    active = df[df["appearances"].fillna(0) >= min_appearances].copy()
    active["goals_per_90"] = active["goals"] / (active["minutes_played"].fillna(0) / 90).replace(0, float("nan"))
    active["assists_per_90"] = active["assists"] / (active["minutes_played"].fillna(0) / 90).replace(0, float("nan"))
    active["goal_contributions"] = active["goals"] + active["assists"]
    active["shot_accuracy"] = (
        active["shots_on_target"] / active["shots_total"].replace(0, float("nan"))
    )
    return active.sort_values("goal_contributions", ascending=False)


def save_processed_players(df: pd.DataFrame) -> None:
    if df.empty:
        return
    collection = get_collection("processed_players")
    records = df.to_dict("records")
    for rec in records:
        collection.update_one(
            {"player_id": rec.get("player_id"), "season": rec.get("season")},
            {"$set": rec},
            upsert=True,
        )
    logger.info("Saved %d processed player records", len(records))
