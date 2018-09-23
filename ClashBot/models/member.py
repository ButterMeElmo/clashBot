from .meta import *

class MEMBER(Base):
    __tablename__ = 'MEMBERS'

    member_tag = Column(String(20), primary_key=True, unique=True)
    member_name = Column(String(20))
    role = Column(String(20))
    trophies = Column(Integer)
    town_hall_level = Column(SmallInteger)
#    last_checked_town_hall = Column(Integer)
    in_clan_currently = Column(Integer)
    in_war_currently = Column(Integer)
#    free_item_day_of_week = Column(SmallInteger)
#    free_item_hour_to_remind = Column(SmallInteger)
#    wants_gift_reminder = Column(SmallInteger)
#    wants_war_reminder = Column(SmallInteger)
