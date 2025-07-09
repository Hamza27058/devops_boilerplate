from elasticsearch import Elasticsearch
from api.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

def index_user(es: Elasticsearch, user: UserResponse):
    """Index a user in Elasticsearch."""
    try:
        es.index(
            index="users",
            id=str(user.id),
            body={
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }
        )
        logger.info(f"Indexed user {user.id} in Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to index user {user.id}: {str(e)}")
        raise

def search_users(es: Elasticsearch, query: str) -> list[UserResponse]:
    """Search for users in Elasticsearch by name or email."""
    try:
        response = es.search(
            index="users",
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name", "email"]
                    }
                }
            }
        )
        users = [
            UserResponse(
                id=int(hit["_id"]),
                name=hit["_source"]["name"],
                email=hit["_source"]["email"],
                created_at=hit["_source"]["created_at"]
            )
            for hit in response["hits"]["hits"]
        ]
        logger.info(f"Found {len(users)} users for query: {query}")
        return users
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise