from .meta import * 

class CLAN(Base):
    __tablename__ = 'CLANS'

    clan_tag = Column(String(20), primary_key=True)
