from .meta import *

class TRADERDATA(Base):
    __tablename__ = 'TRADER_DATA'

    id = Column(Integer, primary_key=True, unique=True)
    value = Column(Integer)

    # 1 is date used in trader calculation
    # 2 is trader cycle length
    # 3 is date this data was last updated