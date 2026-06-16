from dagster import Definitions
from pipelines.assets import (
    standings,
    teams,
    matches,
    players,
    top_stats,
    processed_matches,
    processed_players,
    processed_teams,
    processed_form,
    processed_top_scorers,
    processed_top_assists,
    league_summary,
)
from pipelines.schedules import (
    daily_ingest_schedule,
    daily_process_schedule,
    daily_ingest_job,
    daily_process_job,
    full_pipeline_job,
)

defs = Definitions(
    assets=[
        standings,
        teams,
        matches,
        players,
        top_stats,
        processed_matches,
        processed_players,
        processed_teams,
        processed_form,
        processed_top_scorers,
        processed_top_assists,
        league_summary,
    ],
    jobs=[
        daily_ingest_job,
        daily_process_job,
        full_pipeline_job,
    ],
    schedules=[
        daily_ingest_schedule,
        daily_process_schedule,
    ],
)
