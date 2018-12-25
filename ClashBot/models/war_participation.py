from .meta import *

# from ClashBot.models import WAR, WARATTACK, MEMBER


class WARPARTICIPATION(Base):
    __tablename__ = 'WAR_PARTICIPATIONS'
    __table_args__ = (
        UniqueConstraint('war_id', 'member_tag'),
    )

    id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey('WARS.war_id'))
    member_tag = Column(String(20), ForeignKey('MEMBERS.member_tag'))
    attack_1_id = Column(Integer, ForeignKey('WAR_ATTACKS.id'))
    attack_2_id = Column(Integer, ForeignKey('WAR_ATTACKS.id'))
    # defender_tag = Column(String(20))
    # attacker_attack_number = Column(SmallInteger)
    # attacker_position = Column(SmallInteger)
    # defender_position = Column(SmallInteger)
    # attacker_town_hall = Column(SmallInteger)
    # defender_town_hall = Column(SmallInteger)
    # stars = Column(SmallInteger)
    # destruction_percentage = Column(Float(5, 2))
    # attack_occurred_after = Column(Integer)
    # attack_occurred_before = Column(Integer)
    # order_number = Column(SmallInteger)

    # 0 = no
    # 1 = definitely yes
    # 2 = thought to be, but not positive
    is_clan_war_league_war = Column(SmallInteger)

    attack1 = relationship("WARATTACK", backref="war_participation_1", foreign_keys=[attack_1_id], cascade="all,delete,delete-orphan", single_parent=True)
    attack2 = relationship("WARATTACK", backref="war_participation_2", foreign_keys=[attack_2_id], cascade="all,delete,delete-orphan", single_parent=True)

    war = relationship("WAR", back_populates="war_participations")
    member = relationship("MEMBER", back_populates="war_participations")

    # @property
    # def clan_war_identifier(self):
    #     if self.war is None:
    #         return None
    #     else:
    #         return (self.war.friendly_tag, self.war.enemy_tag, self.war.prep_day_start)

    # def __str__(self):
    #     return 'WARPARTICIPATION val: ' + str(self.war) + ' ' + str(self.member)