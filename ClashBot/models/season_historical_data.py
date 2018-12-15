from .meta import *

class SEASONHISTORICALDATA(Base):
    __tablename__ = "SEASON_HISTORICAL_DATA"
    __table_args__ = (
        UniqueConstraint("season_id", "member_tag"),
    )

    id = Column(Integer, primary_key=True)
    season_id = Column(ForeignKey("SEASONS.season_id"), nullable=False, )
    member_tag = Column(ForeignKey("MEMBERS.member_tag"), nullable=False, )
    troops_donated = Column(Integer)
    troops_received = Column(Integer)
    spells_donated = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)
    
    member = relationship("MEMBER", back_populates="season_historical_data")
    season = relationship("SEASON", back_populates="season_historical_data")

# the purpose of this table is to contain the *known* season data.
# troops are taken from the profile profile, includes ALL even if they left clan and came back (resets counters)
# spells are calculated with the achievement
# attacks and defenses are read from player profile