import logging
import pandas as pd
from db.collections import get_collection

logger = logging.getLogger(__name__)


def load_matches_df(league_id: int | None = None, season: int | None = None) -> pd.DataFrame:
    query: dict = {}
    if league_id:
        query["league.id"] = league_id
    if season:
        query["league.season"] = season

    raw = list(get_collection("matches").find(query, {"_id": 0}))
    if not raw:
        return pd.DataFrame()

    rows = []
    for doc in raw:
        fixture = doc.get("fixture", {})
        league = doc.get("league", {})
        teams = doc.get("teams", {})
        goals = doc.get("goals", {})
        score = doc.get("score", {})

        rows.append({
            "fixture_id": fixture.get("id"),
            "date": fixture.get("date"),
            "status": fixture.get("status", {}).get("short"),
            "venue": fixture.get("venue", {}).get("name"),
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "season": league.get("season"),
            "round": league.get("round"),
            "home_team_id": teams.get("home", {}).get("id"),
            "home_team": teams.get("home", {}).get("name"),
            "away_team_id": teams.get("away", {}).get("id"),
            "away_team": teams.get("away", {}).get("name"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "home_winner": teams.get("home", {}).get("winner"),
            "away_winner": teams.get("away", {}).get("winner"),
            "ht_home": score.get("halftime", {}).get("home"),
            "ht_away": score.get("halftime", {}).get("away"),
        })

    df = pd.DataFrame(rows)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    return df


def compute_form_table(df: pd.DataFrame, last_n: int = 5) -> pd.DataFrame:
    finished = df[df["status"] == "FT"].copy()
    finished = finished.sort_values("date")

    records = []
    for _, row in finished.iterrows():
        records.append({"team_id": row["home_team_id"], "team": row["home_team"],
                        "date": row["date"], "result": "W" if row["home_winner"] else ("L" if row["away_winner"] else "D"),
                        "goals_for": row["home_goals"], "goals_against": row["away_goals"]})
        records.append({"team_id": row["away_team_id"], "team": row["away_team"],
                        "date": row["date"], "result": "W" if row["away_winner"] else ("L" if row["home_winner"] else "D"),
                        "goals_for": row["away_goals"], "goals_against": row["home_goals"]})

    form_df = pd.DataFrame(records)
    form_df = form_df.sort_values("date").groupby("team_id").tail(last_n)
    form_summary = (
        form_df.groupby(["team_id", "team"])
        .agg(
            played=("result", "count"),
            wins=("result", lambda x: (x == "W").sum()),
            draws=("result", lambda x: (x == "D").sum()),
            losses=("result", lambda x: (x == "L").sum()),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
        )
        .reset_index()
    )
    form_summary["points"] = form_summary["wins"] * 3 + form_summary["draws"]
    form_summary["form_string"] = (
        form_df.sort_values("date")
        .groupby("team_id")["result"]
        .apply(lambda x: "".join(x.tail(last_n)))
        .reset_index(drop=True)
    )
    return form_summary.sort_values("points", ascending=False)


def head_to_head(df: pd.DataFrame, team_a_id: int, team_b_id: int) -> pd.DataFrame:
    mask = (
        ((df["home_team_id"] == team_a_id) & (df["away_team_id"] == team_b_id)) |
        ((df["home_team_id"] == team_b_id) & (df["away_team_id"] == team_a_id))
    )
    return df[mask & (df["status"] == "FT")].sort_values("date", ascending=False)


def save_processed_matches(df: pd.DataFrame) -> None:
    if df.empty:
        return
    collection = get_collection("processed_matches")
    records = df.to_dict("records")
    for rec in records:
        if "date" in rec and hasattr(rec["date"], "to_pydatetime"):
            rec["date"] = rec["date"].to_pydatetime()
        collection.update_one(
            {"fixture_id": rec["fixture_id"]},
            {"$set": rec},
            upsert=True,
        )
    logger.info("Saved %d processed match records", len(records))
