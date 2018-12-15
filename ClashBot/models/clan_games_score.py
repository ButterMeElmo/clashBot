from .meta import *

class CLANGAMESSCORE(Base):
    __tablename__ = 'CLAN_GAMES_SCORE'
    __table_args__ = (
        UniqueConstraint('member_tag', 'clan_games_ID'),
    )

    id = Column(Integer, primary_key=True)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    clan_games_ID = Column(Integer, ForeignKey('CLAN_GAMES.clan_games_ID'), nullable=False)
    score = Column(Integer)

    member = relationship("MEMBER", back_populates="clan_games_scores")
    clan_game = relationship("CLANGAME", back_populates="member_scores")

    @property
    def note_key(self):
        return (self.member_tag, self.clan_game.clan_games_ID)