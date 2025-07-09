from sqlalchemy import Column, Integer, ForeignKey
from .base import Base

class UserRole(Base):
    __tablename__ = "user_role"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)
