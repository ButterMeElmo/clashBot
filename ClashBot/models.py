# coding: utf-8
from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
metadata = Base.metadata


class CLAN(Base):
    __tablename__ = 'CLANS'

    clan_tag = Column(String(20), primary_key=True)
    clan_name = Column(String(50))

    

class CLANGAME(Base):
    __tablename__ = 'CLAN_GAMES'

    clan_games_ID = Column(Integer, primary_key=True)
    start_time = Column(Integer, unique=True)
    end_time = Column(Integer)
    top_tier_score = Column(Integer)
    personal_limit = Column(Integer)
    number_of_options = Column(SmallInteger)
    min_town_hall = Column(Integer)


class DISCORDPROPERTY(Base):
    __tablename__ = 'DISCORD_PROPERTIES'

    discord_tag = Column(BigInteger, primary_key=True, unique=True)
    is_troop_donator = Column(Integer)
    has_permission_to_set_war_status = Column(Integer)
    time_last_checked_in = Column(Integer)


class DISCORDNAME(DISCORDPROPERTY):
    __tablename__ = 'DISCORD_NAMES'
    __table_args__ = (
        UniqueConstraint('discord_tag', 'member_tag'),
    )

    discord_tag = Column(ForeignKey('DISCORD_PROPERTIES.discord_tag'), primary_key=True)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False)
    account_order = Column(SmallInteger)

    MEMBER = relationship('MEMBER')


class LASTPROCESSED(Base):
    __tablename__ = 'LAST_PROCESSED'

    count = Column(Integer, primary_key=True, unique=True)
    time = Column(Integer)


class MEMBER(Base):
    __tablename__ = 'MEMBERS'

    member_tag = Column(String(20), primary_key=True, unique=True)
    member_name = Column(String(20))
    role = Column(String(20))
    trophies = Column(Integer)
    town_hall_level = Column(SmallInteger)
    last_checked_town_hall = Column(Integer)
    in_clan_currently = Column(Integer)
    in_war_currently = Column(Integer)
    free_item_day_of_week = Column(SmallInteger)
    free_item_hour_to_remind = Column(SmallInteger)
    wants_gift_reminder = Column(SmallInteger)
    wants_war_reminder = Column(SmallInteger)


class ACCOUNTNAME(MEMBER):
    __tablename__ = 'ACCOUNT_NAMES'
    __table_args__ = (
        UniqueConstraint('member_tag', 'account_name'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True)
    account_name = Column(String(20))


class SCANNEDDATATIME(Base):
    __tablename__ = 'SCANNED_DATA_TIMES'

    scanned_data_index = Column(Integer, primary_key=True)
    time = Column(Integer)


class SEASON(Base):
    __tablename__ = 'SEASONS'
    __table_args__ = (
        UniqueConstraint('start_time', 'end_time'),
    )

    season_ID = Column(Integer, primary_key=True)
    start_time = Column(Integer)
    end_time = Column(Integer)


class SEASONHISTORICALDATUM(Base):
    __tablename__ = 'SEASON_HISTORICAL_DATA'
    __table_args__ = (
        UniqueConstraint('season_ID', 'member_tag'),
    )

    season_ID = Column(Integer, primary_key=True, nullable=False)
    member_tag = Column(String(20), primary_key=True, nullable=False)
    troops_donated = Column(Integer)
    troops_received = Column(Integer)
    spells_donated = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)


class WAR(Base):
    __tablename__ = 'WARS'
    __table_args__ = (
        UniqueConstraint('friendly_tag', 'enemy_tag', 'prep_day_start'),
    )

    war_id = Column(Integer, primary_key=True)
    friendly_tag = Column(String(20))
    enemy_tag = Column(String(20))
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


class ADDORREMOVEFROMWARROSTER(Base):
    __tablename__ = 'ADD_OR_REMOVE_FROM_WAR_ROSTER'

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), nullable=False, unique=True)
    time_requested = Column(Integer)
    change_number = Column(Integer, primary_key=True)
    add_to_roster = Column(SmallInteger)
    remove_from_roster = Column(SmallInteger)

    MEMBER = relationship('MEMBER', uselist=False)


class CALCULATEDTROOPSSPELLSSIEGE(Base):
    __tablename__ = 'CALCULATED_TROOPS_SPELLS_SIEGE'
    __table_args__ = (
        UniqueConstraint('season_id', 'clan_tag', 'member_tag', 'scanned_data_index'),
    )

    season_id = Column(Integer, primary_key=True, nullable=False)
    clan_tag = Column(String(20), primary_key=True, nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    scanned_data_index = Column(Integer)
    donated_all = Column(Integer)
    received_all = Column(Integer)
    donated_troops = Column(Integer)
    received_troops = Column(Integer)
    donated_spells = Column(Integer)
    received_spells = Column(Integer)
    donated_siege = Column(Integer)
    received_siege = Column(Integer)

    MEMBER = relationship('MEMBER')


class CLANGAMESSCORE(Base):
    __tablename__ = 'CLAN_GAMES_SCORE'
    __table_args__ = (
        UniqueConstraint('member_tag', 'clan_games_ID'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    clan_games_ID = Column(Integer, primary_key=True, nullable=False)
    score = Column(Integer)

    MEMBER = relationship('MEMBER')


class SCANNEDDATUM(Base):
    __tablename__ = 'SCANNED_DATA'
    __table_args__ = (
        UniqueConstraint('member_tag', 'scanned_data_index'),
    )

    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    scanned_data_index = Column(ForeignKey('SCANNED_DATA_TIMES.scanned_data_index'), primary_key=True, nullable=False)
    troops_donated_monthly = Column(Integer)
    troops_received_monthly = Column(Integer)
    spells_donated_achievement = Column(Integer)
    troops_donated_achievement = Column(Integer)
    clan_games_points = Column(Integer)
    attacks_won = Column(Integer)
    defenses_won = Column(Integer)
    town_hall_level = Column(SmallInteger)

    MEMBER = relationship('MEMBER')
    SCANNED_DATA_TIME = relationship('SCANNEDDATATIME')


class TROOPDONATION(Base):
    __tablename__ = 'TROOP_DONATIONS'
    __table_args__ = (
        UniqueConstraint('season_id', 'clan_tag', 'member_tag'),
    )

    season_id = Column(Integer, primary_key=True, nullable=False)
    clan_tag = Column(String(20), primary_key=True, nullable=False)
    member_tag = Column(ForeignKey('MEMBERS.member_tag'), primary_key=True, nullable=False)
    donated = Column(Integer)
    received = Column(Integer)

    MEMBER = relationship('MEMBER')

if __name__ == '__main__':
	# Create an engine that stores data in the local directory's
	# sqlalchemy_example.db file.
	engine = create_engine('sqlite:///clashData.db')
	 
	# Create all tables in the engine. This is equivalent to "Create Table"
	# statements in raw SQL.
	Base.metadata.create_all(engine)
