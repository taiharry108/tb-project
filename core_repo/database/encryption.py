from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="files")
    filename = Column(String)

    finished_processing = Column(DateTime)
    last_update = Column(DateTime, default=datetime.now())


class PrivateKey(Base):
    __tablename__ = "private_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="private_keys")
