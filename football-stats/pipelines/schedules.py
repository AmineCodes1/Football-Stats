from dagster import ScheduleDefinition, define_asset_job, AssetSelection

daily_ingest_job = define_asset_job(
    name="daily_ingest_job",
    selection=AssetSelection.groups("ingestion"),
    description="Fetch all raw data from API-Football and store in MongoDB.",
)

daily_process_job = define_asset_job(
    name="daily_process_job",
    selection=AssetSelection.groups("processing"),
    description="Run all Pandas transformations and save processed results.",
)

full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    selection=AssetSelection.groups("ingestion", "processing"),
    description="Full pipeline: ingest from API then process all data.",
)

daily_ingest_schedule = ScheduleDefinition(
    job=daily_ingest_job,
    cron_schedule="0 6 * * *",
    name="daily_ingest_schedule",
    description="Fetch fresh data from API-Football every day at 06:00 UTC.",
)

daily_process_schedule = ScheduleDefinition(
    job=daily_process_job,
    cron_schedule="0 7 * * *",
    name="daily_process_schedule",
    description="Run processing pipeline every day at 07:00 UTC (after ingestion).",
)
