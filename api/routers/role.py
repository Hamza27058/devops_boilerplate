from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from api.services.role_service import store_role, get_all_roles, get_role_by_id, update_role, soft_deleted_role, restore_role, hard_soft_deleted_role, get_all_soft_deleted_roles
from typing import List

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("", response_model=RoleResponse, summary="Store a new role")
async def store_role_endpoint(role: RoleCreate, db: Session = Depends(get_db)):
    try:
        return store_role(db, role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[RoleResponse], summary="Get all roles")
async def get_all_roles_endpoint(db: Session = Depends(get_db)):
    return get_all_roles(db)

@router.get("/{role_id}", response_model=RoleResponse, summary="Get role by ID")
async def get_role_by_id_endpoint(role_id: int, db: Session = Depends(get_db)):
    role = get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=RoleResponse, summary="Update a role")
async def update_role_endpoint(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = update_role(db, role_id, role)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.post("/soft-delete/{role_id}", response_model=dict, summary="Soft delete a role")
async def soft_deleted_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    success = soft_deleted_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found or cannot be deleted")
    return {"message": f"Role {role_id} soft deleted"}

@router.post("/restore/{role_id}", response_model=dict, summary="Restore a role")
async def restore_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    success = restore_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found or not soft deleted")
    return {"message": f"Role {role_id} restored"}

@router.delete("/{role_id}", response_model=dict, summary="Hard delete a role")
async def hard_soft_deleted_role_endpoint(role_id: int, db: Session = Depends(get_db)):
    success = hard_soft_deleted_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found or cannot be deleted")
    return {"message": f"Role {role_id} hard deleted"}

@router.get("/soft-deleted", response_model=List[RoleResponse], summary="Get all soft deleted roles")
async def get_all_soft_deleted_roles_endpoint(db: Session = Depends(get_db)):
    return get_all_soft_deleted_roles(db)


