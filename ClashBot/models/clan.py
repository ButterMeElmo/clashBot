# coding: utf-8
from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
metadata = Base.metadata


class CLAN(Base):
    __tablename__ = 'CLANS'

    clan_tag = Column(String(20), primary_key=True)
