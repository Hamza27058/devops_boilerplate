from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List
from .base import Base

class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    is_default = Column(Boolean, default=False)
    can_deleted = Column(Boolean, default=True)
    created_at = Column(Date, server_default=func.current_date())
    updated_at = Column(Date, onupdate=func.current_date())
    deleted_at = Column(Date, nullable=True)
    users = relationship("User", secondary="user_role", back_populates="roles")

    def __repr__(self):
        return f"<Role(name={self.name})>"
