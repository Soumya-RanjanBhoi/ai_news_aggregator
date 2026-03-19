from sqlalchemy import Column, Integer, String, JSON
from src.database.database import Base


class User_Db(Base):

    __tablename__ = "users_database"
    id = Column(Integer,autoincrement=True,nullable=False,primary_key=True,unique=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    preferences = Column(JSON, nullable=True)
