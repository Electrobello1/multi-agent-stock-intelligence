from sqlalchemy import (
    Column,
    Integer,
    String
)

from Backend.database.connection import Base



class Asset(Base):

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)

    symbol = Column(String, index=True)

    company_name = Column(String, index=True)

    exchange = Column(String)

    asset_type = Column(String)