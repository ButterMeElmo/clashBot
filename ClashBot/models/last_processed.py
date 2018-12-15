from .meta import *

class LASTPROCESSED(Base):
    __tablename__ = 'LAST_PROCESSED'

    id = Column(Integer, primary_key=True, unique=True)
    time = Column(Integer)

