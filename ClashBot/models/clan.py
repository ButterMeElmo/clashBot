from .meta import *
from sqlalchemy.orm.collections import attribute_mapped_collection


class CLAN(Base):
    __tablename__ = 'CLANS'

    clan_tag = Column(String(20), primary_key=True)
    clan_name = Column(String(50))

    members = relationship("MEMBER",
                           back_populates="clan",
                           collection_class=attribute_mapped_collection('member_tag')
                           )

    wars_as_friendly = relationship("WAR",
                                    back_populates="friendly_clan",
                                    foreign_keys="WAR.friendly_tag",
                                    collection_class=attribute_mapped_collection('war_id')
                                    )

    wars_as_enemy = relationship("WAR",
                                 back_populates="enemy_clan",
                                 foreign_keys="WAR.enemy_tag",
                                 collection_class=attribute_mapped_collection('war_id')
                                 )

    # children = relationship("Child", back_populates="parent")
