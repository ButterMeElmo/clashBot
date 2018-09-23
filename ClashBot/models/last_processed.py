from .meta import *

class LASTPROCESSED(Base):
    __tablename__ = 'LAST_PROCESSED'

    count = Column(Integer, primary_key=True, unique=True)
    time = Column(Integer)

