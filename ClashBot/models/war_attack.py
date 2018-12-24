from .meta import *


class WARATTACK(Base):
    __tablename__ = 'WAR_ATTACKS'
    __table_args__ = (
        UniqueConstraint('war_id', 'attacker_tag', 'attacker_attack_number'),
    )

    id = Column(Integer, primary_key=True)

    war_id = Column(ForeignKey('WARS.war_id'))
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=True)
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

    # 0 = no
    # 1 = definitely yes
    # 2 = thought to be, but not positive
    is_clan_war_league_attack = Column(SmallInteger)

    war = relationship("WAR", backref="war_attack")
    member = relationship("MEMBER", backref="war_attack")

    # def __str__(self):
    #     return '{}: {} stars {}% destruction defender:{}'.format(self.war.clan_war_identifier, self.stars, self.destruction_percentage, self.defender_tag)