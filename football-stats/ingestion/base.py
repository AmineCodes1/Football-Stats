import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import RAPIDAPI_KEY, API_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def api_get(endpoint: str, params: dict) -> dict:
    if not RAPIDAPI_KEY:
        raise RuntimeError(
            "RAPIDAPI_KEY is not set. Add it to your .env file or Replit Secrets."
        )

    url = f"{API_BASE_URL}/{endpoint}"
    headers = {
        "x-apisports-key": RAPIDAPI_KEY,
    }

    session = build_session()
    logger.info("GET %s params=%s", url, params)

    response = session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    errors = data.get("errors", {})
    if errors:
        rate_err = errors.get("rateLimit", "")
        if rate_err:
            logger.warning("Rate limit hit — waiting 65 seconds: %s", rate_err)
            time.sleep(65)
            response = session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            errors = data.get("errors", {})
        if errors:
            raise ValueError(f"API returned errors: {errors}")

    remaining = response.headers.get("x-ratelimit-requests-remaining")
    if remaining is not None and int(remaining) < 3:
        logger.warning("Rate limit nearly exhausted (%s remaining) — waiting 65s", remaining)
        time.sleep(65)

    return data


def paginate(endpoint: str, params: dict, max_pages: int | None = None) -> list[dict]:
    results = []
    page = 1
    while True:
        page_params = {**params}
        if page > 1:
            page_params["page"] = page
        data = api_get(endpoint, page_params)
        response_data = data.get("response", [])
        results.extend(response_data)

        paging = data.get("paging", {})
        total_pages = paging.get("total", 1)
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)
        logger.info("Fetched page %d / %d from %s (%d records)", page, total_pages, endpoint, len(response_data))

        if page >= total_pages:
            break
        page += 1
        time.sleep(7)

    return results
