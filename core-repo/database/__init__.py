from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .crud_service import CRUDService
from .database_service import DatabaseService
