from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from redis import Redis
from elasticsearch import Elasticsearch
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from api.config import settings
import logging

logger = logging.getLogger(__name__)

# Database dependency
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        # Test connection on session creation
        db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        yield db
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise
    finally:
        db.close()

# Redis dependency
@retry(stop=stop_after_attempt(5), wait=wait_fixed(2), retry=retry_if_exception_type(ConnectionError))
def get_redis():
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    redis_client.ping()
    logger.info("Redis connection successful")
    return redis_client

# Elasticsearch dependency
@retry(stop=stop_after_attempt(5), wait=wait_fixed(2), retry=retry_if_exception_type(ConnectionError))
def get_elasticsearch():
    es_client = Elasticsearch([settings.ELASTICSEARCH_URL])
    es_client.ping()
    logger.info("Elasticsearch connection successful")
    return es_client
