# Football Statistics Platform

A full-stack football data pipeline: API-Football → MongoDB → Dagster orchestration → Metabase dashboards.

## Quick Start

### 1. Set up credentials

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required values:
- `RAPIDAPI_KEY` — from [RapidAPI API-Football](https://rapidapi.com/api-sports/api/api-football)
- `MONGODB_URI` — from [MongoDB Atlas](https://www.mongodb.com/atlas) or local Docker

### 2. Install Python dependencies

```bash
cd football-stats
pip install -r requirements.txt
```

### 3. Start MongoDB + Metabase (Docker)

```bash
docker-compose up -d
```

### 4. Run a manual full data pull

```bash
python ingestion/fetch_all.py
```

Optional flags:
```bash
python ingestion/fetch_all.py --league 140 --season 2024   # La Liga 2024
```

### 5. Run all data processing

```bash
python processing/process_all.py
```

### 6. Launch Dagster orchestration UI

```bash
dagster dev
```

Open http://localhost:3001 to see the Dagster UI.

---

## Project Structure

```
football-stats/
├── ingestion/
│   ├── base.py              # HTTP client, retry logic, rate limiting
│   ├── fetch_matches.py     # Match fixtures
│   ├── fetch_players.py     # Player stats, top scorers, top assists
│   ├── fetch_standings.py   # League standings
│   ├── fetch_teams.py       # Team info and statistics
│   └── fetch_all.py         # Manual full-pull entry point
│
├── pipelines/
│   ├── assets.py            # Dagster software-defined assets
│   ├── schedules.py         # Cron schedules and job definitions
│   └── definitions.py       # Dagster Definitions object (entry point)
│
├── processing/
│   ├── clean_matches.py     # Match normalization, form tables, H2H
│   ├── clean_players.py     # Player normalization, rankings, per-90 stats
│   ├── stats.py             # xG estimation, team stats, league summary
│   └── process_all.py       # Manual processing entry point
│
├── db/
│   ├── connection.py        # MongoDB client singleton
│   └── collections.py       # Collection helpers + index setup
│
├── config/
│   └── settings.py          # All config from environment variables
│
├── docker-compose.yml       # MongoDB + Metabase services
├── requirements.txt
├── pyproject.toml           # Dagster entry point config
└── .env.example             # Environment variable template
```

---

## MongoDB Collections

| Collection | Contents |
|---|---|
| `matches` | Raw fixture data from API-Football |
| `players` | Raw player stats per season |
| `teams` | Team info per league/season |
| `standings` | League standings tables |
| `top_scorers` | Top goal scorers list |
| `top_assists` | Top assists list |
| `team_statistics` | Per-team detailed stats |
| `processed_matches` | Cleaned, flat match records |
| `processed_players` | Normalized players with per-90 stats |
| `processed_teams` | Aggregated W/D/L/GD/points |
| `processed_form` | Last-N match form per team |
| `processed_league_summary` | League-level summary stats |

---

## Dagster Jobs & Schedules

| Job | What it does | Schedule |
|---|---|---|
| `daily_ingest_job` | Fetch all raw data from API-Football | Daily at 06:00 UTC |
| `daily_process_job` | Run Pandas transformations | Daily at 07:00 UTC |
| `full_pipeline_job` | Ingest + process in one run | Manual |

---

## Supported Leagues

| League ID | Name |
|---|---|
| 39 | English Premier League |
| 140 | La Liga |
| 135 | Serie A |
| 78 | Bundesliga |
| 61 | Ligue 1 |
| 2 | UEFA Champions League |

Change `DEFAULT_LEAGUE_ID` in `.env` to switch leagues.

---

## Metabase Setup

1. Open http://localhost:3000 after running `docker-compose up -d`
2. Complete the Metabase setup wizard
3. Add a new database connection:
   - Type: **MongoDB**
   - Host: `mongodb` (Docker network name)
   - Port: `27017`
   - Database: `football_stats`
   - Username: `admin`
   - Password: `password`
4. Start exploring the `processed_*` collections for dashboards

### Suggested Dashboards

- **Match Performance** — goals per match, results distribution, home/away advantage
- **Player Leaderboard** — top scorers, assists, goal contributions, per-90 stats
- **Team Comparison** — points, GD, form, win rate side by side
- **League Standings** — live table with form column
