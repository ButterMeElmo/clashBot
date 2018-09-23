from .meta import *

class SCANNEDDATA(Base):
    __tablename__ = 'SCANNED_DATA'
    __table_args__ = (
        UniqueConstraint('member_tag', 'scanned_data_index'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    scanned_data_index = Column(ForeignKey('SCANNED_DATA_TIMES.scanned_data_index'), primary_key=True, nullable=False)
    troops_donated_monthly = Column(Integer)
    troops_received_monthly = Column(Integer)
    spells_donated_achievement = Column(Integer)
    troops_donated_achievement = Column(Integer)
    clan_games_points = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)
    town_hall_level = Column(SmallInteger)

    MEMBER = relationship('MEMBER')
    SCANNED_DATA_TIME = relationship('SCANNEDDATATIME')
