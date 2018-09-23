from .meta import *

class TROOPDONATION(Base):
    __tablename__ = 'TROOP_DONATIONS'
    __table_args__ = (
        UniqueConstraint('season_id', 'clan_tag', 'member_tag'),
    )

    season_id = Column(Integer, primary_key=True, nullable=False)
    clan_tag = Column(String(20), primary_key=True, nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    donated = Column(Integer)
    received = Column(Integer)

    MEMBER = relationship('MEMBER')
