from .meta import *

class DISCORDACCOUNT(Base):
    __tablename__ = 'DISCORD_ACCOUNTS'

    id = Column(Integer, primary_key=True)
    discord_tag = Column(BigInteger, unique=True, nullable=False)
    is_troop_donator = Column(Integer, nullable=False)
    has_permission_to_set_war_status = Column(Integer)
    time_last_checked_in = Column(Integer)
    trader_shop_reminder_hour = Column(SmallInteger)

    discord_clash_links = relationship("DISCORDCLASHLINK", back_populates="discord_account")