from .meta import *


class ACCOUNTNAME(Base):
    __tablename__ = 'ACCOUNT_NAMES'
    __table_args__ = (
        UniqueConstraint('member_tag', 'account_name'),
    )

    id = Column(Integer, primary_key=True)
    member_tag = Column(String(20), ForeignKey('MEMBERS.member_tag'))
    account_name = Column(String(20))

    # member = relationship(
    #                       "MEMBER",
    #                       back_populates="all_names"
    #                      )
