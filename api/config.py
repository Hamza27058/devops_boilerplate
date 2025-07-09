import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "myapp")
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
    ELASTICSEARCH_URL = f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"

    def __init__(self):  # Changed from __post_init__ to __init__
        logger.info(f"Environment variables: POSTGRES_HOST={self.POSTGRES_HOST}, POSTGRES_PORT={self.POSTGRES_PORT}, "
                    f"POSTGRES_USER={self.POSTGRES_USER}, POSTGRES_DB={self.POSTGRES_DB}")
        logger.info(f"Database URL: {self.DATABASE_URL}")
        logger.info(f"Redis: {self.REDIS_HOST}:{self.REDIS_PORT}")
        logger.info(f"Elasticsearch: {self.ELASTICSEARCH_URL}")

settings = Settings()
