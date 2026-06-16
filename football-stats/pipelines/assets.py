"""
Dagster software-defined assets for each data type.
Each asset corresponds to one fetch + one processing step.
"""
import logging
from dagster import asset, AssetExecutionContext, Output, MetadataValue
from config.settings import DEFAULT_LEAGUE_ID, DEFAULT_SEASON

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ingestion assets
# ---------------------------------------------------------------------------

@asset(
    group_name="ingestion",
    description="Fetch league standings from API-Football and store in MongoDB.",
)
def standings(context: AssetExecutionContext) -> Output[int]:
    from ingestion.fetch_standings import fetch_standings
    count = fetch_standings(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    return Output(count, metadata={"records_upserted": MetadataValue.int(count)})


@asset(
    group_name="ingestion",
    description="Fetch team list from API-Football and store in MongoDB.",
)
def teams(context: AssetExecutionContext) -> Output[int]:
    from ingestion.fetch_teams import fetch_teams
    count = fetch_teams(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    return Output(count, metadata={"records_upserted": MetadataValue.int(count)})


@asset(
    group_name="ingestion",
    description="Fetch all match fixtures from API-Football and store in MongoDB.",
)
def matches(context: AssetExecutionContext) -> Output[int]:
    from ingestion.fetch_matches import fetch_matches
    count = fetch_matches(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    return Output(count, metadata={"records_upserted": MetadataValue.int(count)})


@asset(
    group_name="ingestion",
    description="Fetch player statistics from API-Football and store in MongoDB.",
)
def players(context: AssetExecutionContext) -> Output[int]:
    from ingestion.fetch_players import fetch_players
    count = fetch_players(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    return Output(count, metadata={"records_upserted": MetadataValue.int(count)})


@asset(
    group_name="ingestion",
    description="Fetch top scorers and top assists lists.",
    deps=["players"],
)
def top_stats(context: AssetExecutionContext) -> Output[dict]:
    from ingestion.fetch_players import fetch_top_scorers, fetch_top_assistants
    scorers = fetch_top_scorers(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    assists = fetch_top_assistants(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    return Output(
        {"scorers": scorers, "assists": assists},
        metadata={
            "top_scorers": MetadataValue.int(scorers),
            "top_assists": MetadataValue.int(assists),
        },
    )


# ---------------------------------------------------------------------------
# Processing assets (depend on ingestion)
# ---------------------------------------------------------------------------

@asset(
    group_name="processing",
    deps=["matches"],
    description="Clean and normalize match data, compute form tables.",
)
def processed_matches(context: AssetExecutionContext) -> Output[int]:
    from processing.clean_matches import load_matches_df, save_processed_matches
    df = load_matches_df(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    save_processed_matches(df)
    return Output(len(df), metadata={"rows_processed": MetadataValue.int(len(df))})


@asset(
    group_name="processing",
    deps=["players"],
    description="Clean and normalize player data, compute rankings.",
)
def processed_players(context: AssetExecutionContext) -> Output[int]:
    from processing.clean_players import load_players_df, compute_player_rankings, save_processed_players
    df = load_players_df(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    ranked = compute_player_rankings(df)
    save_processed_players(ranked)
    return Output(len(ranked), metadata={"rows_processed": MetadataValue.int(len(ranked))})


@asset(
    group_name="processing",
    deps=["processed_matches"],
    description="Compute aggregated team stats (W/D/L, GD, points, form).",
)
def processed_teams(context: AssetExecutionContext) -> Output[int]:
    from processing.clean_matches import load_matches_df
    from processing.stats import compute_team_stats
    from db.collections import get_collection
    df = load_matches_df(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    if df.empty:
        return Output(0)
    team_stats = compute_team_stats(df)
    col = get_collection("processed_teams")
    for rec in team_stats.to_dict("records"):
        rec["league_id"] = DEFAULT_LEAGUE_ID
        rec["season"] = DEFAULT_SEASON
        col.update_one({"team_id": rec["team_id"], "season": DEFAULT_SEASON}, {"$set": rec}, upsert=True)
    return Output(len(team_stats), metadata={"rows_processed": MetadataValue.int(len(team_stats))})


@asset(
    group_name="processing",
    deps=["processed_matches"],
    description="Compute recent form table per team from last N matches.",
)
def processed_form(context: AssetExecutionContext) -> Output[int]:
    from processing.clean_matches import load_matches_df, compute_form_table
    from db.collections import get_collection
    df = load_matches_df(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    if df.empty:
        return Output(0, metadata={"rows_processed": MetadataValue.int(0)})
    form_df = compute_form_table(df)
    col = get_collection("processed_form")
    for rec in form_df.to_dict("records"):
        rec["league_id"] = DEFAULT_LEAGUE_ID
        rec["season"] = DEFAULT_SEASON
        col.update_one({"team_id": rec["team_id"], "season": DEFAULT_SEASON}, {"$set": rec}, upsert=True)
    return Output(len(form_df), metadata={"rows_processed": MetadataValue.int(len(form_df))})


@asset(
    group_name="processing",
    deps=["processed_players"],
    description="Build top 20 scorers table with rank, goals, assists and per-90 metrics.",
)
def processed_top_scorers(context: AssetExecutionContext) -> Output[int]:
    from processing.stats import compute_top_scorers, save_top_scorers
    records = compute_top_scorers(DEFAULT_LEAGUE_ID, DEFAULT_SEASON, limit=20)
    save_top_scorers(records)
    return Output(len(records), metadata={"rows_processed": MetadataValue.int(len(records))})


@asset(
    group_name="processing",
    deps=["top_stats"],
    description="Build top 20 assists table with rank, assists, goals and per-90 metrics.",
)
def processed_top_assists(context: AssetExecutionContext) -> Output[int]:
    from processing.stats import compute_top_assists, save_top_assists
    records = compute_top_assists(DEFAULT_LEAGUE_ID, DEFAULT_SEASON, limit=20)
    save_top_assists(records)
    return Output(len(records), metadata={"rows_processed": MetadataValue.int(len(records))})


@asset(
    group_name="processing",
    deps=["processed_matches", "processed_players"],
    description="Compute and store league-level summary statistics.",
)
def league_summary(context: AssetExecutionContext) -> Output[dict]:
    from processing.stats import compute_league_summary, save_league_summary
    summary = compute_league_summary(DEFAULT_LEAGUE_ID, DEFAULT_SEASON)
    save_league_summary(summary)
    return Output(summary, metadata={
        "total_matches": MetadataValue.int(summary.get("total_matches", 0)),
        "total_goals": MetadataValue.int(summary.get("total_goals", 0)),
        "avg_goals_per_match": MetadataValue.float(summary.get("avg_goals_per_match", 0.0)),
    })
