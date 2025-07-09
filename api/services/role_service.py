from sqlalchemy.orm import Session
from sqlalchemy import func
from api.models import Role
from api.schemas.role import RoleCreate, RoleUpdate, RoleResponse
import logging
from typing import List

logger = logging.getLogger(__name__)

def store_role(db: Session, role: RoleCreate) -> Role:
    db_role = Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    logger.info(f"Stored role {db_role.id}")
    return db_role

def get_all_roles(db: Session) -> List[Role]:
    return db.query(Role).filter(Role.deleted_at == None).all()

def get_role_by_id(db: Session, role_id: int) -> Role:
    return db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()

def update_role(db: Session, role_id: int, role: RoleUpdate) -> Role:
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
    if not db_role:
        return None
    update_data = role.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    db.commit()
    db.refresh(db_role)
    logger.info(f"Updated role {role_id}")
    return db_role

def soft_deleted_role(db: Session, role_id: int) -> bool:
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
    if not db_role or not db_role.can_deleted:
        return False
    db_role.deleted_at = func.now()
    db.commit()
    logger.info(f"Soft deleted role {role_id}")
    return True

def restore_role(db: Session, role_id: int) -> bool:
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at != None).first()
    if not db_role:
        return False
    db_role.deleted_at = None
    db.commit()
    logger.info(f"Restored role {role_id}")
    return True

def hard_soft_deleted_role(db: Session, role_id: int) -> bool:
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role or not db_role.can_deleted:
        return False
    db.delete(db_role)
    db.commit()
    logger.info(f"Hard deleted role {role_id}")
    return True

def get_all_soft_deleted_roles(db: Session) -> List[Role]:
    return db.query(Role).filter(Role.deleted_at != None).all()

