from .meta import *


class DISCORDCLASHLINK(Base):
    __tablename__ = 'DISCORD_CLASH_LINKS'
    __table_args__ = (
        UniqueConstraint('discord_tag', 'member_tag'),
    )

    id = Column(Integer, primary_key=True)
    discord_tag = Column(ForeignKey('DISCORD_ACCOUNTS.discord_tag'), nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    account_order = Column(SmallInteger)

    discord_account = relationship("DISCORDACCOUNT", back_populates="discord_clash_links")
    clash_account = relationship("MEMBER", back_populates="discord_clash_links")
    #
    # member = relationship('MEMBER', back_populates='discord_names')
    # discord_properties = relationship("DISCORDUSER", back_populates='discord_names')

