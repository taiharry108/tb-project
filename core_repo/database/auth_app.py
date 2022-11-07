from sqlalchemy import Boolean, Column, String, Integer
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String)

    files = relationship("File", back_populates="user")
    private_keys = relationship("PrivateKey", uselist=False, back_populates="user")
    history_mangas = relationship("History", back_populates="user")
