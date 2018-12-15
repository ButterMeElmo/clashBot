from .meta import *

class SCANNEDDATA(Base):
    __tablename__ = 'SCANNED_DATA'
    __table_args__ = (
        UniqueConstraint('member_tag', 'timestamp'),
    )

    id = Column(Integer, primary_key=True)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    # scanned_data_index = Column(ForeignKey('SCANNED_DATA_TIMES.scanned_data_index'), nullable=False)
    troops_donated_monthly = Column(Integer)
    troops_received_monthly = Column(Integer)
    spells_donated_achievement = Column(Integer)
    troops_donated_achievement = Column(Integer)
    clan_games_points_achievement = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)
    town_hall_level = Column(SmallInteger)
    timestamp = Column(Integer)

    # MEMBER = relationship('MEMBER')
    # SCANNED_DATA_TIME = relationship('SCANNEDDATATIME')

    # scanned_data_time = relationship("SCANNEDDATATIME",
    #                                  back_populates="scanned_data"
    #                                  )

    # member = relationship("MEMBER",
    #                        back_populates="scanned_data"
    #                        )