from .meta import *

class SCANNEDDATATIME(Base):
    __tablename__ = 'SCANNED_DATA_TIMES'

    scanned_data_index = Column(Integer, primary_key=True)
    time = Column(Integer)
