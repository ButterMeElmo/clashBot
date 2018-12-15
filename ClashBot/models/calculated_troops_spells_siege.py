from .meta import *

class CALCULATEDTROOPSSPELLSSIEGE(Base):
    __tablename__ = 'CALCULATED_TROOPS_SPELLS_SIEGE'
    __table_args__ = (
        UniqueConstraint('season_id', 'clan_tag', 'member_tag'),
    )

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, nullable=False)
    clan_tag = Column(String(20), nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    donated_all = Column(Integer)
    received_all = Column(Integer)
    donated_troops = Column(Integer)
    received_troops = Column(Integer)
    donated_spells = Column(Integer)
    received_spells = Column(Integer)
    donated_siege = Column(Integer)
    received_siege = Column(Integer)

    MEMBER = relationship('MEMBER')

# this uses scanned data?
# or season historical data?
# to attempt to determine what were actual troops, siege, or spells
# both donations and received