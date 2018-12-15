from .meta import *

class SEASONHISTORICALDATA(Base):
    __tablename__ = 'SEASON_HISTORICAL_DATA'
    __table_args__ = (
        UniqueConstraint('season_ID', 'member_tag', 'scanned_data_index'),
    )

    id = Column(Integer, primary_key=True)
    season_ID = Column(Integer, nullable=False)
    member_tag = Column(String(20), nullable=False)
    scanned_data_index = Column(Integer)
    troops_donated = Column(Integer)
    troops_received = Column(Integer)
    spells_donated = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)

# the purpose of this table is to contain the known season data.
# troops are taken from ?? (hopefully achievement too?)
# spells are calculated with the achievement
# was scanned data index in here for any reason
# this contains a subset of calculated + attacks and defenses