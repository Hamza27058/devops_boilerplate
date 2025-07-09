from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from api.schemas.role import RoleResponse

class UserCreate(BaseModel):
    name: str
    email: str
    is_default: bool = False
    can_deleted: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice",
                "email": "alice@example.com",
                "is_default": False,
                "can_deleted": True
            }
        }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_default: Optional[bool] = None
    can_deleted: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice Updated",
                "email": "alice.updated@example.com",
                "is_default": True,
                "can_deleted": False
            }
        }

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_default: bool
    can_deleted: bool
    created_at: date
    updated_at: Optional[date] = None
    deleted_at: Optional[date] = None
    roles: List[RoleResponse]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "is_default": False,
                "can_deleted": True,
                "created_at": "2025-07-02",
                "updated_at": None,
                "deleted_at": None,
                "roles": []
            }
        }

class CacheData(BaseModel):
    data: str

    class Config:
        json_schema_extra = {
            "example": {
                "data": "Some cached information"
            }
        }

class CustomResponse(BaseModel):
    code: int
    message: str
    data: List[UserResponse]

    class Config:
        from_attributes = True
