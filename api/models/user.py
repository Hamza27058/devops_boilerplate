from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List
from .base import Base

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    is_default = Column(Boolean, default=False)
    can_deleted = Column(Boolean, default=True)
    created_at = Column(Date, server_default=func.current_date())
    updated_at = Column(Date, onupdate=func.current_date())
    deleted_at = Column(Date, nullable=True)
    roles = relationship("Role", secondary="user_role", back_populates="users")

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"
