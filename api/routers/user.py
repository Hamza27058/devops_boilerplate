from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from elasticsearch import Elasticsearch
from api.dependencies import get_db, get_redis, get_elasticsearch
from api.schemas.user import UserCreate, UserUpdate, UserResponse, CacheData, CustomResponse
from api.schemas.health import HealthStatus
from api.services.user_service import store_user, get_all_users, get_user_by_id, update_user, soft_deleted_user, restore_user, hard_soft_deleted_user, get_all_soft_deleted_users
from api.services.redis_service import cache_user_data, get_cached_user_data
from api.services.elasticsearch_service import index_user, search_users
from api.models import User, Role, UserRole
from typing import List, Tuple
import logging

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

# Static routes first
@router.get("/health", response_model=dict)
async def health_check(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    es: Elasticsearch = Depends(get_elasticsearch)
):
    return {"status": "All services are up"}

@router.get("/health-details", response_model=HealthStatus, summary="Detailed health check for all services")
async def health_check_details(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    es: Elasticsearch = Depends(get_elasticsearch)
):
    """Check connectivity to PostgreSQL, Redis, and Elasticsearch with detailed status."""
    status = {"postgresql": "connected", "redis": "connected", "elasticsearch": "connected"}
    details = {}

    try:
        db.execute("SELECT 1")
        details["postgresql"] = "Successfully executed SELECT 1"
    except Exception as e:
        status["postgresql"] = "failed"
        details["postgresql"] = f"Error: {str(e)}"
        logger.error(f"PostgreSQL health check failed: {str(e)}")

    try:
        redis.ping()
        details["redis"] = "PING returned PONG"
    except Exception as e:
        status["redis"] = "failed"
        details["redis"] = f"Error: {str(e)}"
        logger.error(f"Redis health check failed: {str(e)}")

    try:
        es_health = es.cluster.health()
        status["elasticsearch"] = "connected" if es_health["status"] in ["green", "yellow"] else "failed"
        details["elasticsearch"] = f"Cluster health status: {es_health['status']}"
    except Exception as e:
        status["elasticsearch"] = "failed"
        details["elasticsearch"] = f"Error: {str(e)}"
        logger.error(f"Elasticsearch health check failed: {str(e)}")

    if any(s == "failed" for s in status.values()):
        raise HTTPException(status_code=503, detail=status)

    return HealthStatus(**status, details=details)

@router.get("/soft-deleted", response_model=CustomResponse, summary="Get all soft deleted users")
async def get_all_soft_deleted_users_endpoint(db: Session = Depends(get_db)):
    logger.info("Accessing /users/soft-deleted endpoint")
    users = get_all_soft_deleted_users(db)
    if not users:
        logger.warning("No soft-deleted users found")
    return CustomResponse(code=200, message="get_all_soft_deleted_users", data=users)

@router.post("", response_model=CustomResponse, summary="Store a new user")
async def store_user_endpoint(user: UserCreate, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), es: Elasticsearch = Depends(get_elasticsearch)):
    try:
        db_user = store_user(db, user)
        index_user(es, db_user)

        try:
            if redis.exists("all_users"):
                redis.delete("all_users")
                logger.info("Cache for 'all_users' invalidated due to new user creation.")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")

        return CustomResponse(code=201, message="store_user", data=[db_user])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=CustomResponse, summary="Get all users")
async def get_all_users_endpoint(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    cache_key = "all_users"
    cached_data = get_cached_user_data(redis, cache_key)
    if cached_data is not None:
        logger.info(f"Raw cached data: {cached_data}")
        try:
            users = [UserResponse(**user) for user in cached_data]
            logger.info(f"Retrieved cached data for all users")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to process cached data: {str(e)}")
            users = []
    else:
        logger.info("Cache miss, querying database for all users")
        users_from_db = get_all_users(db)
      
        users = [UserResponse.from_orm(u) for u in users_from_db]
        try:
           
            data_to_cache = [user.dict() for user in users]
            cache_user_data(redis, "all_users", data_to_cache, ttl=300)
            logger.info("All users data cached")
        except Exception as e:
            logger.error(f"Failed to cache data: {str(e)}")
    return CustomResponse(code=200, message="get_all_users", data=users)

# Parameterized routes after static routes
@router.get("/{user_id}", response_model=CustomResponse, summary="Get user by ID")
async def get_user_by_id_endpoint(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return CustomResponse(code=200, message="get_user_by_id", data=[user])

@router.put("/{user_id}", response_model=CustomResponse, summary="Update a user")
async def update_user_endpoint(user_id: int, user: UserUpdate, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), es: Elasticsearch = Depends(get_elasticsearch)):
    db_user = update_user(db, user_id, user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    index_user(es, db_user)

    try:
        if redis.exists("all_users"):
            redis.delete("all_users")
            logger.info("Cache for 'all_users' invalidated due to user update.")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")

    return CustomResponse(code=200, message="update_user", data=[db_user])

@router.put("/soft-delete/{user_id}", response_model=CustomResponse, summary="Soft delete a user")
async def soft_deleted_user_endpoint(user_id: int, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), es: Elasticsearch = Depends(get_elasticsearch)):
    success, message = soft_deleted_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    try:
        es.delete(index="users", id=str(user_id))
        logger.info(f"Soft deleted user {user_id} from Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to soft delete user {user_id} from Elasticsearch: {str(e)}")

    try:
        if redis.exists("all_users"):
            redis.delete("all_users")
            logger.info("Cache for 'all_users' invalidated due to user soft-delete.")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")

    return CustomResponse(code=200, message="soft_deleted_user", data=[])

@router.post("/restore/{user_id}", response_model=CustomResponse, summary="Restore a user")
async def restore_user_endpoint(user_id: int, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    success = restore_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or not soft deleted")
    
    try:
        if redis.exists("all_users"):
            redis.delete("all_users")
            logger.info("Cache for 'all_users' invalidated due to user restore.")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")

    return CustomResponse(code=200, message="restore_user", data=[])

@router.delete("/{user_id}", response_model=CustomResponse, summary="Hard delete a user")
async def hard_soft_deleted_user_endpoint(user_id: int, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), es: Elasticsearch = Depends(get_elasticsearch)):
    success = hard_soft_deleted_user(db, es, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot be deleted")

    try:
        if redis.exists("all_users"):
            redis.delete("all_users")
            logger.info("Cache for 'all_users' invalidated due to user hard-delete.")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")

    return CustomResponse(code=200, message="hard_soft_deleted_user", data=[])

@router.post("/cache/{user_id}", response_model=CustomResponse)
async def cache_user_data_endpoint(user_id: int, data: CacheData, redis: Redis = Depends(get_redis)):
    cache_user_data(redis, user_id, data.data)
    return CustomResponse(code=200, message="cache_user_data", data=[])

@router.get("/cache/{user_id}", response_model=CustomResponse)
async def get_cached_user_data_endpoint(user_id: int, redis: Redis = Depends(get_redis)):
    data = get_cached_user_data(redis, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Cached data not found")
    return CustomResponse(code=200, message="get_cached_user_data", data=[{"user_id": user_id, "data": data}])

@router.get("/search", response_model=CustomResponse)
async def search_users_endpoint(q: str, es: Elasticsearch = Depends(get_elasticsearch)):
    users = search_users(es, q)
    return CustomResponse(code=200, message="search_users", data=users)

@router.post("/assign-role/{user_id}", response_model=CustomResponse, summary="Assign a role to a user")
async def assign_role_to_user(user_id: int, role_id: int, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), es: Elasticsearch = Depends(get_elasticsearch)):
    try:
        logger.info(f"Attempting to assign role {role_id} to user {user_id}")
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User {user_id} retrieved: {user}")

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        logger.info(f"Role {role_id} retrieved: {role}")

        if role in user.roles:
            raise HTTPException(status_code=400, detail="Role already assigned to user")
        logger.info(f"Role {role_id} not assigned to user {user_id}, proceeding to append")

        user.roles.append(role)
        logger.info(f"Role {role_id} appended to user {user_id}")
        db.commit()
        logger.info(f"Database commit successful for user {user_id}")

        try:
            if redis.exists("all_users"):
                redis.delete("all_users")
                logger.info("Cache for 'all_users' invalidated.")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for 'all_users': {str(e)}")


        user_response = UserResponse.from_orm(user)
        logger.info(f"UserResponse created for user {user_id}: {user_response}")
        try:
            index_user(es, user_response)
            logger.info(f"User {user_id} indexed in Elasticsearch")
        except Exception as e:
            logger.warning(f"Failed to index user {user_id} in Elasticsearch: {str(e)}")
        return CustomResponse(code=200, message="assign_role_to_user", data=[user_response])
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Exception in assign_role_to_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
