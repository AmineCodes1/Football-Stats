import logging
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from config.settings import MONGODB_URI, MONGODB_DB

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        try:
            _client.admin.command("ping")
            logger.info("Connected to MongoDB at %s", MONGODB_URI)
        except ConnectionFailure as e:
            logger.error("MongoDB connection failed: %s", e)
            raise
    return _client


def get_db() -> Database:
    return get_client()[MONGODB_DB]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")
