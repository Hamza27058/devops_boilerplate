from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class RoleCreate(BaseModel):
    name: str
    is_default: Optional[bool] = False
    can_deleted: Optional[bool] = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "admin",
                "is_default": False,
                "can_deleted": True
            }
        }

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    can_deleted: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "superadmin",
                "is_default": True,
                "can_deleted": False
            }
        }

class RoleResponse(BaseModel):
    id: int
    name: str
    is_default: bool
    can_deleted: bool
    created_at: date
    updated_at:  Optional[date] = None
    deleted_at: Optional[date] = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "admin",
                "is_default": False,
                "can_deleted": True,
                "created_at": "2025-07-02",
                "updated_at": "2025-07-02",
                "deleted_at": None,
                "users": [{"id": 1, "name": "Alice", "email": "alice@example.com", "is_default": False, "can_deleted": True, "created_at": "2025-07-02", "updated_at": "2025-07-02", "deleted_at": None}]
            }
        }
