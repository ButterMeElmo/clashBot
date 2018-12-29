from .meta import *

class TRADERITEM(Base):
    __tablename__ = 'TRADER_ITEMS'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(30))
    day_in_rotation = Column(SmallInteger)
    cost = Column(SmallInteger)
