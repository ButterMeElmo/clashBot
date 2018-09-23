from .meta import *

class CLANGAMESSCORE(Base):
    __tablename__ = 'CLAN_GAMES_SCORE'
    __table_args__ = (
        UniqueConstraint('member_tag', 'clan_games_ID'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    clan_games_ID = Column(Integer, primary_key=True, nullable=False)
    score = Column(Integer)

    MEMBER = relationship('MEMBER')
