#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import datetime
import pytest
import clashBot.supercell_data_fetcher
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


@pytest.mark.parametrize("time_string, result", [
    ('1984-06-02T19:05:00.000Z', 455051100.0),
    ('2018-06-11 08:00:00+00:00', 1528704000),
])
def test_convertTime(time_string, result):
    assert clashSaveData.convertTime(time_string) == result


@pytest.mark.parametrize("clan_name, clan_tag", [
    ('Clan Name Example', 'ia7jvV'),
])
def test_addClanToDB(db, clan_name, clan_tag):
    cursor = db.cursor()
    clashSaveData.addClanToDB(cursor, clan_name, clan_tag)

    cursor.execute('SELECT * FROM CLANS')
    results = cursor.fetchall()
    desired_results = [(clan_tag, clan_name)]
    assert results == desired_results


@pytest.mark.parametrize("tag, name, role, townHallLevel, lastSeenInWar", [
    ('taghere', 'namehere', None, 11, 48539),
    ('taghesdgre', 'namehese', 'Elder', None, None),
    pytest.param('taghesdgre', 'namehese', 'Elder', 3, 1064867,
                 marks=pytest.mark.xfail(reason='the third one doesn\'t work yet')),
])
def test_addMemberToDB(db, tag, name, role, townHallLevel, lastSeenInWar):
    cursor = db.cursor()
    clashSaveData.addMemberToDB(
        cursor, tag, name, role, townHallLevel, lastSeenInWar)

    cursor.execute('SELECT * FROM MEMBERS')
    results = cursor.fetchall()
    desired_results = [(tag, name, role, None, townHallLevel,
                        lastSeenInWar, 1, 0, None, None, None)]
    assert results == desired_results

    cursor.execute('SELECT * FROM ACCOUNT_NAMES')
    results = cursor.fetchall()
    desired_results = [(tag, name)]
    assert results == desired_results


test_member_tag_1 = 'auierighrawg'
test_member_tag_2 = 'reowbwrv'
test_clan_tag = '#ia7jvV'


@pytest.fixture(scope='function')
def db_with_clan_and_members(db):
    cursor = db.cursor()
    clashSaveData.addClanToDB(cursor, 'Clan Name Example', test_clan_tag)
    clashSaveData.addMemberToDB(
        cursor, test_member_tag_1, 'namehese', 'Elder', None, None)
    clashSaveData.addMemberToDB(
        cursor, test_member_tag_2, 'awegawhrh', 'Co-leader', None, None)
    yield db


@pytest.mark.parametrize("data", [
    ([(test_clan_tag, test_member_tag_1, 10, 0, 1)]),
    ([(test_clan_tag, test_member_tag_2, 1000, 40, 2)]),
    ([(test_clan_tag, test_member_tag_1, 10, 100, 3)]),
    pytest.param(([
        (test_clan_tag, test_member_tag_1, 10, 100, 1),
        (test_clan_tag, test_member_tag_1, 0, 10, 1),
        (test_clan_tag, test_member_tag_1, 10, 100, 3),
    ]), marks=pytest.mark.xfail(reason='Currently I don\'t account for when someone has left and come back')),
])
def test_addDonationsToDB(db_with_clan_and_members, data):
    cursor = db_with_clan_and_members.cursor()

    desired_results_pretransform = {}
    for entry in data:
        clan_tag = entry[0]
        member_tag = entry[1]
        donated = entry[2]
        received = entry[3]
        season_id = entry[4]
        clashSaveData.addDonationsToDB(
            cursor, clan_tag, member_tag, donated, received, season_id)
        if not season_id in desired_results_pretransform:
            desired_results_pretransform[season_id] = {}
        if not member_tag in desired_results_pretransform[season_id]:
            desired_results_pretransform[season_id][member_tag] = [0, 0]
        if donated < desired_results_pretransform[season_id][member_tag][0] or received < desired_results_pretransform[season_id][member_tag][1]:
            desired_results_pretransform[season_id][member_tag][0] += donated
            desired_results_pretransform[season_id][member_tag][1] += received
        else:
            desired_results_pretransform[season_id][member_tag][0] = donated
            desired_results_pretransform[season_id][member_tag][1] = received

    for season_id in desired_results_pretransform:
        for member_tag in desired_results_pretransform[season_id]:
            donated, received = desired_results_pretransform[season_id][member_tag]
            cursor.execute(
                'SELECT * FROM TROOP_DONATIONS WHERE season_id = ? AND member_tag = ?', (season_id, member_tag))
            results = cursor.fetchall()
            desired_results = [
                (season_id, test_clan_tag, member_tag, donated, received)
            ]
            assert results == desired_results


FAKE_WAR = (1, 'awghioe', 'iuawihgeawg', 'result_here', 5,
            26, 16.754, 31.13, 1, 23, 20, 1234, 12345, 123456)


@pytest.mark.parametrize("war_id, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end",
                         [
                             FAKE_WAR
                         ])
def test_addWarToDB(db, war_id, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end):
    cursor = db.cursor()

    clashSaveData.addWarToDB(cursor, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage,
                             enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end)
    cursor.execute('SELECT * FROM WARS')
    results = cursor.fetchall()
    desired_results = [(war_id, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage,
                        enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end)]
    assert results == desired_results

#test_member_tag_1 = 'auierighrawg'
#test_member_tag_2 = 'reowbwrv'
# test_clan_tag = '#ia7jvV'


@pytest.fixture(scope='function')
def db_with_clan_and_members_and_war(db):
    cursor = db.cursor()
    clashSaveData.addClanToDB(cursor, 'Clan Name Example', test_clan_tag)
    clashSaveData.addMemberToDB(
        cursor, test_member_tag_1, 'namehese', 'Elder', None, None)
    clashSaveData.addMemberToDB(
        cursor, test_member_tag_2, 'awegawhrh', 'Co-leader', None, None)
    friendly_tag = FAKE_WAR[1]
    enemy_tag = FAKE_WAR[2]
    result = FAKE_WAR[3]
    friendly_stars = FAKE_WAR[4]
    enemy_stars = FAKE_WAR[5]
    friendly_percentage = FAKE_WAR[6]
    enemy_percentage = FAKE_WAR[7]
    friendly_attacks_used = FAKE_WAR[8]
    enemy_attacks_used = FAKE_WAR[9]
    war_size = FAKE_WAR[10]
    prep_day_start = FAKE_WAR[11]
    war_day_start = FAKE_WAR[12]
    war_day_end = FAKE_WAR[13]
    clashSaveData.addWarToDB(cursor, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage,
                             enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end)
    yield db


@pytest.mark.parametrize("warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime",
                         [
                             (1, 'aweawh', 12, 10, 1, 1760943)
                         ])
def test_createEmptyWarAttack(warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime):
    warAttackDict = {}
    warAttackDict['warID'] = warID
    warAttackDict['attackerTag'] = attackerTag
    warAttackDict['defenderTag'] = None
    warAttackDict['attackerAttackNumber'] = attackNumber
    warAttackDict['attackerPosition'] = attackerPosition
    warAttackDict['defenderPosition'] = None
    warAttackDict['attackerTownHall'] = attackerTownHall
    warAttackDict['defenderTownHall'] = None
    warAttackDict['stars'] = None
    warAttackDict['destructionPercentage'] = None
    warAttackDict['attackOccurredAfter'] = dataTime
    warAttackDict['attackOccurredBefore'] = None
    warAttackDict['orderNumber'] = None
    result = clashSaveData.createEmptyWarAttack(
        warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime)
    assert result == warAttackDict


@pytest.mark.parametrize("warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime, defenderTag, defenderPosition, defenderTownHall, stars, destructionPercentage, attackOccurredAfter, orderNumber",
                         [
                             (1, 'aweawh', 12, 10, 1, 1760943,
                              'wagoehi', 1, 12, 3, 29.485, 128379, 54)
                         ])
def test_addWarAttackToDB(db_with_clan_and_members_and_war, warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime, defenderTag, defenderPosition, defenderTownHall, stars, destructionPercentage, attackOccurredAfter, orderNumber):
    cursor = db_with_clan_and_members_and_war.cursor()

    warAttackDict = clashSaveData.createEmptyWarAttack(
        warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime)
    warAttackDict['defenderTag'] = defenderTag
    warAttackDict['defenderPosition'] = defenderPosition
    warAttackDict['defenderTownHall'] = defenderTownHall
    warAttackDict['stars'] = stars
    warAttackDict['destructionPercentage'] = destructionPercentage
    warAttackDict['attackOccurredAfter'] = attackOccurredAfter
    warAttackDict['orderNumber'] = orderNumber
    clashSaveData.addWarAttackToDB(cursor, warAttackDict)

    cursor.execute('SELECT * FROM WAR_ATTACKS')
    results = cursor.fetchall()
    desired_results = [(warID, attackerTag, defenderTag, attackerAttackNumber, attackerPosition, defenderPosition, attackerTownHall,
                        defenderTownHall, stars, destructionPercentage, attackOccurredAfter, attackOccurredBefore, orderNumber)]
    assert results == desired_results


process_war_end = datetime.datetime(2018, 6, 2)


@pytest.mark.parametrize("patch_datetime_now, process_war_start, desired_results", [
    (
        process_war_end,
        datetime.datetime(2018, 5, 28),
        [
            (1, '#NG97789JF', '#YQPV0CPG', 'lost', 50, 60, 87.85,
             100.0, 22, 27, 20, 1527208860, 1527291660, 1527378060),
            (2, '#NG97789JF', '#209CJ98QQ', 'in progress', 33, 40, 64.4,
             75.4, 17, 23, 20, 1527553665, 1527636465, 1527722865),
            (3, '#NG97789JF', '#C0JQ082U', 'won', 59, 53, 98.4,
             91.25, 32, 27, 20, 1527731402, 1527814202, 1527901570),
            (4, '#NG97789JF', '#G028GUQG', 'in progress', 0, 0,
             0.0, 0.0, 0, 0, 20, 1527905298, 1527988098, 1528074498)
        ]
    ),
    pytest.param(
        process_war_end,
        datetime.datetime(2018, 5, 28),
        [
            (1, '#NG97789JF', '#YQPV0CPG', 'lost', 50, 60, 87.85,
             100.0, 22, 27, 20, 1527208860, 1527291660, 1527378060),
            (2, '#NG97789JF', '#209CJ98QQ', 'lost', 33, 40, 64.4,
             75.4, 17, 23, 20, 1527553665, 1527636465, 1527722865),
            (3, '#NG97789JF', '#C0JQ082U', 'won', 59, 53, 98.4,
             91.25, 32, 27, 20, 1527731402, 1527814202, 1527901570),
            (4, '#NG97789JF', '#G028GUQG', 'in progress', 0, 0,
             0.0, 0.0, 0, 0, 20, 1527905298, 1527988098, 1528074498)
        ], marks=pytest.mark.xfail(reason='the second one is showing "in progress" for some reason')
    )
], indirect=['patch_datetime_now'])
def test_processWar(db, patch_datetime_now, process_war_start, desired_results):
    cursor = db.cursor()
    warFileNames = getDataFromServer.getFileNames(
        'data/warDetailsLog', '.json', process_war_start.timestamp())
    for filename in warFileNames:
        if os.path.exists(filename):
            wars = json.load(open(filename))
            for war in wars:
                clashSaveData.processWar(war, cursor)
    cursor.execute('SELECT * FROM WARS')
    results = cursor.fetchall()
    assert results == desired_results


@pytest.mark.xfail
def test_findPositionAndTownHallForMemberTag(db):
    assert False


@pytest.mark.xfail
def test_getAllMembersTagSupposedlyInClan(db):
    assert False


@pytest.mark.xfail
def test_markMembersNoLongerActive(db):
    assert False


@pytest.mark.xfail
def test_getSeasonIDForUTCTimestamp():
    assert False


@pytest.mark.xfail
def test_processClanProfile(db):
    assert False


@pytest.mark.xfail
def test_addAccountName(db):
    assert False


@pytest.mark.xfail
def test_addScannedDataToDB(db):
    assert False


@pytest.mark.xfail
def test_addMemberFromAchievements(db):
    assert False


@pytest.mark.xfail
def test_processClanPlayerAcievements(db):
    assert False


@pytest.mark.xfail
def test_getNextSeasonTimeStamp():
    assert False


@pytest.mark.xfail
def test_populateSeasons(db):
    assert False


@pytest.mark.xfail
def test_turnClanGamesStringIntoTimestamp():
    assert False


@pytest.mark.xfail
def test_useOldClanGamesData(db):
    assert False


@pytest.mark.xfail
def test_useOldClanProfile(db):
    assert False


@pytest.mark.xfail
def test_useLinkedAccountsStartingPoint(db):
    assert False


@pytest.mark.xfail
def test_importSavedFreeGiftDays(db):
    assert False


@pytest.mark.xfail
def test_getMinAllowableTimeForClanGameData():
    assert False


games_data = [(1, 1513670400, 1513843200, 10000, 500, None, 6), (2, 1513929600, 1514275200, 30000, 2000, None, 6), (3, 1515139200, 1515398400, 20000, 2500, None, 6), (4, 1515830400, 1515916800, 5000, 1000, None, 6), (5, 1516348800, 1516608000, 20000, 2500, None, 6), (6, 1517040000, 1517126400, 5000, 1000, None, 6), (7, 1517299200, 1517817600, 50000, 3000, None, 6), (8, 1517904000, 1518422400, 50000, 3000, None, 6), (9, 1518681600, 1519286400, 75000, 3000, None, 6), (10, 1519718400, 1520236800, 50000, 3000, None, 6),
              (11, 1520496000, 1520841600, 50000, 3000, None, 6), (12, 1521187200, 1521532800, 30000, 2000, None, 6), (13, 1521792000, 1522137600, 50000, 3000, None, 6), (14, 1522396800, 1522742400, 30000, 3000, None, 6), (15, 1523347200, 1523865600, 50000, 4000, None, 6), (16, 1524556800, 1525161600, 50000, 4000, None, 6), (17, 1525766400, 1526371200, 30000, 4000, None, 6), (18, 1526976000, 1527580800, 30000, 4000, None, 6), (19, 1528099200, 1528704000, 30000, 4000, None, 6), (20, 1529308800, 1529913600, 50000, 4000, None, 6)]


@pytest.mark.parametrize("current_games_number, expected_result", [

])
def test_getMaxAllowableTimeForClanGameData(current_games_number, expected_result):
    assert False


@pytest.mark.xfail
def test_DEBUG_ONLY_getMemberNameFromTag(db):
    assert False


@pytest.mark.xfail
def test_processClanGamesData(db):
    assert False


@pytest.mark.parametrize("timestamp", [
    19684376
])
def test_markProcessingTime(db, timestamp):
    cursor = db.cursor()
    clashSaveData.markProcessingTime(cursor, timestamp)

    cursor.execute('SELECT time FROM LAST_PROCESSED WHERE count = 1')
    results = cursor.fetchall()
    desired_results = [(timestamp,)]
    assert results == desired_results


@pytest.mark.parametrize("timestamp", [
    19684376
])
def test_getLastProcessedTime(db, timestamp):
    cursor = db.cursor()

    cursor.execute('SELECT time FROM LAST_PROCESSED WHERE count = 1')
    results = cursor.fetchall()
    desired_results = []
    assert results == desired_results

    clashSaveData.markProcessingTime(cursor, timestamp)
    results = clashSaveData.getLastProcessedTime(cursor)
    desired_results = timestamp
    assert results == desired_results


end_of_data_processing = datetime.datetime(2018, 6, 5)


@pytest.mark.parametrize("end_of_data_processing_time, patch_datetime_now, num_wars", [
    (
        1527941399,
        process_war_end,
        2
    ),
], indirect=['patch_datetime_now'])
def test_saveData(db, patch_datetime_now, end_of_data_processing_time, num_wars):
    cursor = db.cursor()
    clashSaveData.saveData(cursor, end_of_data_processing_time)

    cursor.execute('SELECT * FROM WARS')
    results = cursor.fetchall()
    assert len(results) == 2
