from sqlalchemy.orm import Session, joinedload
from elasticsearch import Elasticsearch
from api.models import User
from api.schemas.user import UserCreate, UserUpdate, UserResponse
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

def store_user(db: Session, user: UserCreate) -> UserResponse:
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Stored user {db_user.id}")
    return UserResponse.from_orm(db_user)

def get_all_users(db: Session) -> list[UserResponse]:
    users = db.query(User).options(joinedload(User.roles)).filter(User.deleted_at.is_(None)).all()
    return [UserResponse.from_orm(user) for user in users]

def get_user_by_id(db: Session, user_id: int) -> UserResponse:
    user = db.query(User).options(joinedload(User.roles)).filter(User.id == user_id, User.deleted_at == None).first()
    if not user:
        return None
    return UserResponse.from_orm(user)

def update_user(db: Session, user_id: int, user: UserUpdate) -> UserResponse:
    db_user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not db_user:
        return None
    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Updated user {user_id}")
    return UserResponse.from_orm(db_user)

def soft_deleted_user(db: Session, user_id: int) -> tuple[bool, str]:
    db_user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not db_user:
        logger.warning(f"User {user_id} not found or already soft-deleted")
        return False, "User not found or already soft-deleted"
    if not db_user.can_deleted:
        logger.warning(f"User {user_id} cannot be deleted (can_deleted=False)")
        return False, "User cannot be deleted"
    db_user.deleted_at = func.current_date()
    db.commit()
    logger.info(f"Soft deleted user {user_id}")
    return True, f"User {user_id} soft deleted"

def restore_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id, User.deleted_at != None).first()
    if not db_user:
        return False
    db_user.deleted_at = None
    db.commit()
    logger.info(f"Restored user {user_id}")
    return True

def hard_soft_deleted_user(db: Session, es: Elasticsearch, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.can_deleted:
        return False
    db.delete(db_user)
    db.commit()
    try:
        es.delete(index="users", id=str(user_id))
        logger.info(f"Hard deleted user {user_id} from Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to delete user {user_id} from Elasticsearch: {str(e)}")
    logger.info(f"Hard deleted user {user_id}")
    return True

def get_all_soft_deleted_users(db: Session) -> list[UserResponse]:
    users = db.query(User).filter(User.deleted_at != None).all()
    logger.info(f"Found {len(users)} soft-deleted users")
    return [UserResponse.from_orm(user) for user in users]
