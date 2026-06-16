"""
Advanced stats computation: xG estimates, team form, head-to-head, league summary.
"""
import logging
import pandas as pd
from db.collections import get_collection
logger = logging.getLogger(__name__)
def estimate_xg(shots_total: float, shots_on_target: float, goals: float) -> float:
    """
    Rough xG estimate using shot data.
    Real xG requires per-shot location data not provided by the free API tier.
    This is a simplified model: on-target shots weighted by historical conversion rate.
    """
    if shots_total == 0:
        return 0.0
    shot_quality = shots_on_target / shots_total if shots_total > 0 else 0
    base_xg = shots_total * 0.10
    quality_adjustment = shot_quality * shots_total * 0.05
    return round(base_xg + quality_adjustment, 2)
def compute_team_stats(matches_df: pd.DataFrame) -> pd.DataFrame:
    finished = matches_df[matches_df["status"] == "FT"].copy()
    home = finished[["home_team_id", "home_team", "home_goals", "away_goals", "home_winner", "away_winner"]].copy()
    home.columns = ["team_id", "team", "goals_for", "goals_against", "win", "loss"]
    away = finished[["away_team_id", "away_team", "away_goals", "home_goals", "away_winner", "home_winner"]].copy()
    away.columns = ["team_id", "team", "goals_for", "goals_against", "win", "loss"]
    combined = pd.concat([home, away], ignore_index=True)
    combined["win"] = combined["win"].fillna(False).astype(bool)
    combined["loss"] = combined["loss"].fillna(False).astype(bool)
    combined["draw"] = ~combined["win"] & ~combined["loss"]
    summary = (
        combined.groupby(["team_id", "team"])
        .agg(
            played=("goals_for", "count"),
            wins=("win", "sum"),
            draws=("draw", "sum"),
            losses=("loss", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
        )
        .reset_index()
    )
    summary["points"] = summary["wins"] * 3 + summary["draws"]
    summary["goal_difference"] = summary["goals_for"] - summary["goals_against"]
    summary["win_rate"] = (summary["wins"] / summary["played"]).round(3)
    return summary.sort_values(["points", "goal_difference"], ascending=False).reset_index(drop=True)
def _best_from_raw(collection_name: str, league_id: int, season: int, stat_key: str) -> dict:
    col = get_collection(collection_name)
    docs = list(col.find({"league_id": league_id, "season": season}, {"player.name": 1, "statistics": 1}))
    if not docs:
        return {}
    best = max(docs, key=lambda d: (d.get("statistics", [{}])[0].get("goals", {}).get(stat_key) or 0))
    value = best.get("statistics", [{}])[0].get("goals", {}).get(stat_key) or 0
    team = best.get("statistics", [{}])[0].get("team", {}).get("name")
    return {"name": best.get("player", {}).get("name"), "value": value, "team": team}
def _best_team(league_id: int, season: int, sort_field: str) -> dict:
    col = get_collection("processed_teams")
    doc = col.find_one({"league_id": league_id, "season": season}, sort=[(sort_field, -1)])
    if not doc:
        return {}
    return {"team": doc.get("team"), "value": doc.get(sort_field)}
def compute_league_summary(league_id: int, season: int) -> dict:
    matches_col = get_collection("processed_matches")
    total_matches = matches_col.count_documents({"league_id": league_id, "season": season, "status": "FT"})
    agg = list(matches_col.aggregate([
        {"$match": {"league_id": league_id, "season": season, "status": "FT"}},
        {"$group": {"_id": None, "total_goals": {"$sum": {"$add": ["$home_goals", "$away_goals"]}}}},
    ]))
    total_goals = agg[0]["total_goals"] if agg else 0
    avg_goals = round(total_goals / total_matches, 2) if total_matches else 0
    top_scorer = _best_from_raw("top_scorers", league_id, season, "total")
    top_assister = _best_from_raw("top_assists", league_id, season, "assists")
    most_wins = _best_team(league_id, season, "wins")
    most_goals = _best_team(league_id, season, "goals_for")
    most_points = _best_team(league_id, season, "points")
    return {
        "league_id": league_id,
        "season": season,
        "total_matches": total_matches,
        "total_goals": total_goals,
        "avg_goals_per_match": avg_goals,
        "top_scorer": top_scorer.get("name"),
        "top_scorer_goals": top_scorer.get("value"),
        "top_scorer_team": top_scorer.get("team"),
        "top_assister": top_assister.get("name"),
        "top_assister_assists": top_assister.get("value"),
        "top_assister_team": top_assister.get("team"),
        "most_wins_team": most_wins.get("team"),
        "most_wins_count": most_wins.get("value"),
        "most_goals_team": most_goals.get("team"),
        "most_goals_count": most_goals.get("value"),
        "most_points_team": most_points.get("team"),
        "most_points_count": most_points.get("value"),
    }
def save_league_summary(summary: dict) -> None:
    get_collection("processed_league_summary").update_one(
        {"league_id": summary["league_id"], "season": summary["season"]},
        {"$set": summary},
        upsert=True,
    )
    logger.info("League summary saved for league=%s season=%s", summary["league_id"], summary["season"])
def compute_top_scorers(league_id: int, season: int, limit: int = 20) -> list:
    raw_col = get_collection("top_scorers")
    docs = list(raw_col.find({"league_id": league_id, "season": season}, {"_id": 0}))
    rows = []
    for doc in docs:
        player = doc.get("player", {})
        stats = doc.get("statistics", [{}])[0]
        games = stats.get("games", {})
        goals = stats.get("goals", {})
        cards = stats.get("cards", {})
        team = stats.get("team", {})
        appearances = games.get("appearences") or 0
        minutes = games.get("minutes") or 0
        total_goals = goals.get("total") or 0
        assists = goals.get("assists") or 0
        rows.append({
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "nationality": player.get("nationality"),
            "age": player.get("age"),
            "position": games.get("position"),
            "team_id": team.get("id"),
            "team_name": team.get("name"),
            "league_id": league_id,
            "season": season,
            "appearances": appearances,
            "minutes_played": minutes,
            "goals": total_goals,
            "assists": assists,
            "goal_contributions": total_goals + assists,
            "goals_per_90": round(total_goals / (minutes / 90), 2) if minutes > 0 else 0,
            "assists_per_90": round(assists / (minutes / 90), 2) if minutes > 0 else 0,
            "yellow_cards": cards.get("yellow") or 0,
            "red_cards": cards.get("red") or 0,
        })
    rows.sort(key=lambda x: x["goals"], reverse=True)
    for rank, row in enumerate(rows[:limit], start=1):
        row["rank"] = rank
    return rows[:limit]
def save_top_scorers(records: list) -> None:
    if not records:
        return
    col = get_collection("processed_top_scorers")
    for rec in records:
        col.update_one(
            {"player_id": rec["player_id"], "season": rec["season"], "league_id": rec["league_id"]},
            {"$set": rec},
            upsert=True,
        )
    logger.info("Saved %d top scorer records", len(records))
def compute_top_assists(league_id: int, season: int, limit: int = 20) -> list:
    raw_col = get_collection("top_assists")
    docs = list(raw_col.find({"league_id": league_id, "season": season}, {"_id": 0}))
    rows = []
    for doc in docs:
        player = doc.get("player", {})
        stats = doc.get("statistics", [{}])[0]
        games = stats.get("games", {})
        goals = stats.get("goals", {})
        cards = stats.get("cards", {})
        team = stats.get("team", {})
        appearances = games.get("appearences") or 0
        minutes = games.get("minutes") or 0
        total_goals = goals.get("total") or 0
        assists = goals.get("assists") or 0
        rows.append({
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "nationality": player.get("nationality"),
            "age": player.get("age"),
            "position": games.get("position"),
            "team_id": team.get("id"),
            "team_name": team.get("name"),
            "league_id": league_id,
            "season": season,
            "appearances": appearances,
            "minutes_played": minutes,
            "goals": total_goals,
            "assists": assists,
            "goal_contributions": total_goals + assists,
            "goals_per_90": round(total_goals / (minutes / 90), 2) if minutes > 0 else 0,
            "assists_per_90": round(assists / (minutes / 90), 2) if minutes > 0 else 0,
            "yellow_cards": cards.get("yellow") or 0,
            "red_cards": cards.get("red") or 0,
        })
    rows.sort(key=lambda x: x["assists"], reverse=True)
    for rank, row in enumerate(rows[:limit], start=1):
        row["rank"] = rank
    return rows[:limit]
def save_top_assists(records: list) -> None:
    if not records:
        return
    col = get_collection("processed_top_assists")
    for rec in records:
        col.update_one(
            {"player_id": rec["player_id"], "season": rec["season"], "league_id": rec["league_id"]},
            {"$set": rec},
            upsert=True,
        )
    logger.info("Saved %d top assists records", len(records))