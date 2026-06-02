import os
from dotenv import load_dotenv

load_dotenv(override=True)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
API_SPORTS_KEY = RAPIDAPI_KEY
RAPIDAPI_HOST = "api-football-v1.p.rapidapi.com"
API_BASE_URL = "https://v3.football.api-sports.io"

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "football_stats")

DEFAULT_LEAGUE_ID = int(os.getenv("DEFAULT_LEAGUE_ID", "39"))
DEFAULT_SEASON = int(os.getenv("DEFAULT_SEASON", "2024"))

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2
