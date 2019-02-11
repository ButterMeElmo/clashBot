from .meta import *


class ADDORREMOVEFROMWARROSTER(Base):
    __tablename__ = 'ADD_OR_REMOVE_FROM_WAR_ROSTER'

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False, unique=True)
    time_requested = Column(Integer)
    change_number = Column(Integer, primary_key=True)
    add_to_roster = Column(SmallInteger)
    remove_from_roster = Column(SmallInteger)

    MEMBER = relationship('MEMBER', uselist=False)
