from .meta import *
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from ClashBot.models import WARPARTICIPATION, WARATTACK

class MEMBER(Base):
    __tablename__ = 'MEMBERS'

    member_tag = Column(String(20), primary_key=True, unique=True)
    role = Column(String(20))
    trophies = Column(Integer)
    town_hall_level = Column(SmallInteger)
#    last_checked_town_hall = Column(Integer)
    last_updated_time = Column(Integer)
    trader_rotation_offset = Column(SmallInteger)
#    free_item_hour_to_remind = Column(SmallInteger)
#    wants_gift_reminder = Column(SmallInteger)
#    wants_war_reminder = Column(SmallInteger)

    king_level = Column(SmallInteger)
    queen_level = Column(SmallInteger)
    warden_level = Column(SmallInteger)

    member_name = Column(String(20))

    clan_tag = Column(String(20), ForeignKey('CLANS.clan_tag'))
    clan = relationship("CLAN",
                        back_populates="members"
                       )

    # member_name = Column(String(20), ForeignKey('ACCOUNT_NAMES.account_name'))
    all_names = relationship(
                                "ACCOUNTNAME",
                                backref="member"
                             )
    scanned_data = relationship("SCANNEDDATA",
                                backref="member",
                                collection_class=attribute_mapped_collection('timestamp')
                                )


    # discord_clash_links = relationship("DISCORDCLASHLINK", back_populates="clash_account")

    clan_games_scores = relationship("CLANGAMESSCORE",
                                     back_populates="member",
                                     collection_class=attribute_mapped_collection('clan_games_id')
                                     )

    season_historical_data = relationship("SEASONHISTORICALDATA", back_populates="member")

    # def get_first_scanned_data_after_time(self, timestamp):
    #     for scanned_data_timestamp in self.scanned_data:
    #         if scanned_data_timestamp > timestamp:
    #             return self.scanned_data[scanned_data_timestamp]
    #     return None
    #
    # def get_last_scanned_data_before_time(self, timestamp):
    #     for scanned_data_timestamp in sorted(self.scanned_data, reverse=True):
    #         if scanned_data_timestamp < timestamp:
    #             return self.scanned_data[scanned_data_timestamp]
    #     return None
    #
    # def get_last_scanned_data_between_timestamps(self, start, finish):
    #     for scanned_data_timestamp in sorted(self.scanned_data, reverse=True):
    #         if start < scanned_data_timestamp < finish:
    #             return self.scanned_data[scanned_data_timestamp]
    #     return None
    #
    # def get_first_scanned_data_between_timestamps(self, start, finish):
    #     for scanned_data_timestamp in self.scanned_data:
    #         if scanned_data_timestamp > start and scanned_data_timestamp < finish:
    #             return self.scanned_data[scanned_data_timestamp]
    #     return None
    #
    # def get_all_scanned_data_between_timestamps(self, start, finish):
    #     result = []
    #     for scanned_data_timestamp in self.scanned_data:
    #         if scanned_data_timestamp > start and scanned_data_timestamp < finish:
    #             result.append(self.scanned_data[scanned_data_timestamp])
    #     return result

    # don't use this one
    war_participations = relationship("WARPARTICIPATION",
                                        back_populates="member",
                                        collection_class=attribute_mapped_collection('war.clan_war_identifier')
                                        )

    # wars_participated_in = association_proxy("war_participations", "war",
    #                                          creator=lambda _, war:
    #                                              WARPARTICIPATION(
    #                                                  war=war,
    #                                                  # attack1=WARATTACK(attacker_attack_number=1, war=war),
    #                                                  # attack2=WARATTACK(attacker_attack_number=2, war=war),
    #                                              )
    #                                          )

    discord_clash_links = relationship("DISCORDCLASHLINK", back_populates="clash_account")