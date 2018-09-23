from .meta import *

class CALCULATEDTROOPSSPELLSSIEGE(Base):
    __tablename__ = 'CALCULATED_TROOPS_SPELLS_SIEGE'
    __table_args__ = (
        UniqueConstraint('season_id', 'clan_tag', 'member_tag', 'scanned_data_index'),
    )

    season_id = Column(Integer, primary_key=True, nullable=False)
    clan_tag = Column(String(20), primary_key=True, nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    scanned_data_index = Column(Integer)
    donated_all = Column(Integer)
    received_all = Column(Integer)
    donated_troops = Column(Integer)
    received_troops = Column(Integer)
    donated_spells = Column(Integer)
    received_spells = Column(Integer)
    donated_siege = Column(Integer)
    received_siege = Column(Integer)

    MEMBER = relationship('MEMBER')
