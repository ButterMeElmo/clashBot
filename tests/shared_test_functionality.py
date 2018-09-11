#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import datetime
import pytest
import getDataFromServer
import clashSaveData
from helper_for_testing import patch_datetime_now
import json

@pytest.fixture(scope='function')
def db(tmpdir):
	file = os.path.join(tmpdir.strpath, "test.db")
	conn = sqlite3.connect(file)
	creationString = """CREATE TABLE WARS (war_id INTEGER PRIMARY KEY, friendly_tag VARCHAR(20), enemy_tag VARCHAR(20), result VARCHAR(11), friendly_stars SMALLINT(3), enemy_stars SMALLINT(3), friendly_percentage DOUBLE(5,2), enemy_percentage DOUBLE(5,2), friendly_attacks_used SMALLINT(3), enemy_attacks_used SMALLINT(3), war_size SMALLINT(3), prep_day_start UNSIGNED INT(11), war_day_start UNSIGNED INT(11), war_day_end UNSIGNED INT(11), UNIQUE(friendly_tag, enemy_tag, prep_day_start) ON CONFLICT REPLACE);

			CREATE TABLE CLANS (clan_tag VARCHAR(20) UNIQUE, clan_name VARCHAR(50));

			CREATE TABLE WAR_ATTACKS (war_id INTEGER, attacker_tag VARCHAR(20), defender_tag VARCHAR(20), attacker_attack_number SMALLINT(3), attacker_position SMALLINT(3), defender_position SMALLINT(3), attacker_town_hall SMALLINT(3), defender_town_hall SMALLINT(3), stars SMALLINT(3), destruction_percentage DOUBLE(5,2), attack_occurred_after UNSIGNED INT(11), attack_occurred_before UNSIGNED INT(11), order_number SMALLINT(3), UNIQUE(war_id, attacker_tag, attacker_attack_number) ON CONFLICT REPLACE);

			CREATE TABLE MEMBERS (member_tag VARCHAR(20) NOT NULL PRIMARY KEY, member_name VARCHAR(20), role VARCHAR(20), trophies MEDIUMINT(5), town_hall_level SMALLINT(3), last_checked_town_hall UNSIGNED INT(11), in_clan_currently INTEGER, in_war_currently INTEGER, free_item_day_of_week SMALLINT(3), free_item_hour_to_remind SMALLINT(3), wants_gift_reminder SMALLINT(1), UNIQUE(member_tag) ON CONFLICT REPLACE);

			CREATE TABLE TROOP_DONATIONS (season_id MEDIUMINT(10), clan_tag VARCHAR(20), member_tag VARCHAR(20) NOT NULL, donated MEDIUMINT(5), received MEDIUMINT(6), FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(season_id, clan_tag, member_tag) ON CONFLICT REPLACE);

			CREATE TABLE CLAN_GAMES (clan_games_ID INTEGER PRIMARY KEY, start_time UNSIGNED INT(11), end_time UNSIGNED INT(11), top_tier_score MEDIUMINT(6), personal_limit MEDIUMINT(6), number_of_options SMALLINT(3), min_town_hall INTEGER, UNIQUE(start_time) ON CONFLICT REPLACE);

			CREATE TABLE CLAN_GAMES_SCORE (member_tag VARCHAR(20) NOT NULL, clan_games_ID INTEGER, score INTEGER, FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(member_tag, clan_games_ID) ON CONFLICT REPLACE);

			CREATE TABLE ACCOUNT_NAMES (member_tag VARCHAR(20) NOT NULL, account_name VARCHAR(20), FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(member_tag, account_name) ON CONFLICT REPLACE);

			CREATE TABLE SCANNED_DATA(member_tag VARCHAR(20) NOT NULL, time UNSIGNED INT(11), troops_donated MEDIUMINT(6), troops_received MEDIUMINT(6), clan_games_points MEDIUMINT(6), FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(member_tag, time) ON CONFLICT REPLACE);

			CREATE TABLE SEASONS (season_ID INTEGER PRIMARY KEY, start_time UNSIGNED INT(11), end_time UNSIGNED INT(11), UNIQUE(start_time, end_time) ON CONFLICT REPLACE);

			CREATE TABLE LAST_PROCESSED (count INTEGER PRIMARY KEY, time UNSIGNED INT(11), UNIQUE(count) ON CONFLICT REPLACE);

			CREATE TABLE ADD_TO_WAR (member_tag VARCHAR(20) NOT NULL, time_requested UNSIGNED INT(11), change_number INTEGER, FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(member_tag) ON CONFLICT REPLACE);

			CREATE TABLE REMOVE_FROM_WAR (member_tag VARCHAR(20) NOT NULL, time_requested UNSIGNED INT(11), change_number INTEGER, FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), UNIQUE(member_tag) ON CONFLICT REPLACE);

			CREATE TABLE DISCORD_PROPERTIES (discord_tag BIGINT(25) NOT NULL PRIMARY KEY, is_troop_donator INTEGER, time_last_checked_in UNSIGNED INT(11), UNIQUE(discord_tag) ON CONFLICT REPLACE);

			CREATE TABLE DISCORD_NAMES (discord_tag BIGINT(25), member_tag VARCHAR(20) NOT NULL, FOREIGN KEY(member_tag) REFERENCES MEMBERS(member_tag), FOREIGN KEY(discord_tag) REFERENCES DISCORD_PROPERTIES(discord_tag), UNIQUE(discord_tag, member_tag) ON CONFLICT REPLACE);
			"""
	conn.executescript(creationString)
	conn.cursor().execute("PRAGMA foreign_keys = ON")
	yield conn
	conn.close()  

#@pytest.mark.parametrize("start_of_data_processing_time, patch_datetime_now", [
#		(
#			int(datetime.datetime(2018, 6, 2).timestamp()),
#			datetime.datetime(2018, 6, 3), 
#		),
#	], indirect=['patch_datetime_now'])

start_of_data_processing_time = int(datetime.datetime(2018, 6, 2).timestamp())
@pytest.fixture(scope='function')
def db_filled_out(monkeypatch, db):
	
	NOW = datetime.datetime(2018, 6, 3)
	class mydatetime:
		@classmethod
		def utcfromtimestamp(cls, param):
			return cls.utcfromtimestamp(param)
		def utcnow():
			return NOW
	monkeypatch.setattr(datetime, 'datetime', mydatetime)	



	cursor = db.cursor()

	clashSaveData.saveData(cursor, start_of_data_processing_time)
#	assert True
	yield db

def test_new_db(db_filled_out):
	cursor = db_filled_out.cursor()
	cursor.execute('SELECT * FROM WARS')
	results = cursor.fetchall()

	assert len(results) == 2



