from .meta import *

class SEASONHISTORICALDATA(Base):
    __tablename__ = 'SEASON_HISTORICAL_DATA'
    __table_args__ = (
        UniqueConstraint('season_ID', 'member_tag'),
    )

    season_ID = Column(Integer, primary_key=True, nullable=False)
    member_tag = Column(String(20), primary_key=True, nullable=False)
    troops_donated = Column(Integer)
    troops_received = Column(Integer)
    spells_donated = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)
