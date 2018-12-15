from .meta import *

class CLANGAME(Base):
    __tablename__ = 'CLAN_GAMES'

    clan_games_ID = Column(Integer, primary_key=True)
    start_time = Column(Integer, unique=True)
    end_time = Column(Integer)
    top_tier_score = Column(Integer)
    personal_limit = Column(Integer)
    number_of_options = Column(SmallInteger)
    min_town_hall = Column(Integer)

    member_scores = relationship("CLANGAMESSCORE",
                                 back_populates="clan_game"
                                 )
