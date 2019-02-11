from .meta import *


class WAR(Base):
    __tablename__ = 'WARS'
    __table_args__ = (
        UniqueConstraint('friendly_tag', 'enemy_tag', 'prep_day_start'),
    )

    war_id = Column(Integer, primary_key=True)
    friendly_tag = Column(String(20), ForeignKey('CLANS.clan_tag'))
    enemy_tag = Column(String(20), ForeignKey('CLANS.clan_tag'))
    result = Column(String(11))
    friendly_stars = Column(SmallInteger)
    enemy_stars = Column(SmallInteger)
    friendly_percentage = Column(Float(5, 2))
    enemy_percentage = Column(Float(5, 2))
    friendly_attacks_used = Column(SmallInteger)
    enemy_attacks_used = Column(SmallInteger)
    war_size = Column(SmallInteger)
    prep_day_start = Column(Integer)
    war_day_start = Column(Integer)
    war_day_end = Column(Integer)

    is_clan_war_league_war = Column(SmallInteger)

    war_attacks = relationship("WARATTACK", back_populates="war")
    # friendly_clan = relationship("CLAN", back_populates="wars")

    friendly_clan = relationship("CLAN", back_populates="wars_as_friendly", foreign_keys=friendly_tag)
    enemy_clan = relationship("CLAN", back_populates="wars_as_enemy", foreign_keys=enemy_tag)

    @property
    def clan_war_identifier(self):
        return (self.friendly_tag, self.enemy_tag, int(self.prep_day_start))

    war_participations = relationship("WARPARTICIPATION",
                                      back_populates="war",
                                      # collection_class=attribute_mapped_collection('war_id')
                                      )
    # members_in_war = association_proxy("war_participations", "member")

    # def __str__(self):
    #     return str(self.clan_war_identifier)
