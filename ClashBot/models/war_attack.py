from .meta import *

from ClashBot.models import WAR

class WARATTACK(WAR):
    __tablename__ = 'WAR_ATTACKS'
    __table_args__ = (
        UniqueConstraint('war_id', 'attacker_tag', 'attacker_attack_number'),
    )

    war_id = Column(ForeignKey('WARS.war_id'), primary_key=True)
    attacker_tag = Column(String(20))
    defender_tag = Column(String(20))
    attacker_attack_number = Column(SmallInteger)
    attacker_position = Column(SmallInteger)
    defender_position = Column(SmallInteger)
    attacker_town_hall = Column(SmallInteger)
    defender_town_hall = Column(SmallInteger)
    stars = Column(SmallInteger)
    destruction_percentage = Column(Float(5, 2))
    attack_occurred_after = Column(Integer)
    attack_occurred_before = Column(Integer)
    order_number = Column(SmallInteger)
