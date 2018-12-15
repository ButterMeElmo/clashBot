from .meta import *

class SEASON(Base):
    __tablename__ = 'SEASONS'
    __table_args__ = (
        UniqueConstraint('start_time', 'end_time'),
    )

    season_id = Column(Integer, primary_key=True)
    start_time = Column(Integer)
    end_time = Column(Integer)

    season_historical_data = relationship("SEASONHISTORICALDATA", back_populates="season")