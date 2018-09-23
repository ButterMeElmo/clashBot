from .meta import *

class DISCORDPROPERTY(Base):
    __tablename__ = 'DISCORD_PROPERTIES'

    discord_tag = Column(BigInteger, primary_key=True, unique=True)
    is_troop_donator = Column(Integer)
    has_permission_to_set_war_status = Column(Integer)
    time_last_checked_in = Column(Integer)
