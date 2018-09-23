from .meta import *
from ClashBot.models import MEMBER

class ACCOUNTNAME(MEMBER):
    __tablename__ = 'ACCOUNT_NAMES'
    __table_args__ = (
        UniqueConstraint('member_tag', 'account_name'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True)
    account_name = Column(String(20))

