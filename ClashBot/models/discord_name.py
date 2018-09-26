from .meta import *

from ClashBot.models import DISCORDPROPERTY

class DISCORDNAME(DISCORDPROPERTY):
    __tablename__ = 'DISCORD_NAMES'
    __table_args__ = (
        UniqueConstraint('discord_tag', 'member_tag'),
    )

    discord_tag = Column(ForeignKey('DISCORD_PROPERTIES.discord_tag'), primary_key=True)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    account_order = Column(SmallInteger)

    MEMBER = relationship('MEMBER')
