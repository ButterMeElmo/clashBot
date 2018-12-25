#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
from sqlite3 import Error
import time
import dateutil.parser as dp
import json
import random
import unittest
import pytz
import datetime
import dateutil
import date_fetcher_formatter
import config_strings

from ClashBot import DateFetcherFormatter, MyConfigBot
from ClashBot.models import DISCORDCLASHLINK, MEMBER, WARATTACK, WAR, DISCORDACCOUNT, WARPARTICIPATION

from sqlalchemy.sql.expression import func

db_file = "clashData.db"
#currentSeasonIDs = {}


class NoDataDuringTimeSpanException(Exception):
    pass


class NoActiveClanWarLeagueWar(Exception):
    pass


class NoActiveClanWar(Exception):
    pass


class DatabaseAccessor:

    def __init__(self, session):

        self.session = session

    def get_discord_ids_of_members_who_are_th12(self, clan_tag=MyConfigBot.my_clan_tag):
        discord_clash_links = self.session.query(DISCORDCLASHLINK) \
                    .join(MEMBER) \
                    .filter(MEMBER.town_hall_level == 12) \
                    .filter(MEMBER.clan_tag == clan_tag) \
                    .all()

        actual_results = set()

        for discord_clan_link in discord_clash_links:
            print(discord_clan_link.clash_account.member_name)
            actual_results.add(str(discord_clan_link.discord_tag))

        return actual_results

    def get_today_cwl_war(self):
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.is_clan_war_league_war == 1) \
            .filter(WAR.war_day_start <= current_time) \
            .filter(WAR.war_day_end >= current_time).one_or_none()
        if war_instance is None:
            raise NoActiveClanWarLeagueWar()
        return war_instance

    def get_tomorrow_cwl_war(self):
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.is_clan_war_league_war == 1) \
            .filter(WAR.prep_day_start <= current_time) \
            .filter(WAR.war_day_start >= current_time).one_or_none()
        if war_instance is None:
            raise NoActiveClanWarLeagueWar()
        return war_instance

    def get_cwl_roster_and_war_today(self):
        war_instance = self.get_today_cwl_war()
        return self.session.query(WARPARTICIPATION) \
            .filter(WARPARTICIPATION.war == war_instance).all(), war_instance

    def get_cwl_roster_and_war_tomorrow(self):
        war_instance = self.get_tomorrow_cwl_war()
        return self.session.query(WARPARTICIPATION) \
            .filter(WARPARTICIPATION.war == war_instance).all(), war_instance

    def is_today_cwl_roster_complete(self):
        roster, _ = self.get_cwl_roster_and_war_today()
        return len(roster) == 15

    def is_tomorrow_cwl_roster_complete(self):
        roster, _ = self.get_cwl_roster_and_war_tomorrow()
        return len(roster) == 15

    def add_member_to_cwl(self, member_instance, war_instance):
        # todo this data should be added to the exporter
        war_participation_instance = WARPARTICIPATION()
        war_participation_instance.war = war_instance
        war_participation_instance.member = member_instance
        # 2 means we think
        war_participation_instance.is_clan_war_league_war = 2
        attack_1_instance = WARATTACK()
        attack_1_instance.attacker_attack_number = 1
        attack_1_instance.war = war_instance
        attack_1_instance.member = member_instance
        attack_1_instance.attacker_tag = member_instance.member_tag
        war_participation_instance.attack1 = attack_1_instance
        self.session.add(war_participation_instance)

    def remove_member_from_current_cwl(self, member_instance, war_instance):
        for war_participation_instance in war_instance.war_participations:
            if war_participation_instance.member == member_instance:
                self.session.delete(war_participation_instance)
                break

    def get_members_in_clan_with_name(self, member_name, clan_tag=MyConfigBot.my_clan_tag):
        return self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag) \
            .filter(func.upper(MEMBER.member_name) == member_name).all()

    def get_timestamps_for_current_war(self):

        current_timestamp = DateFetcherFormatter.get_utc_timestamp()

        war_end_time = self.session.query(WAR.war_day_end) \
            .filter(WAR.war_day_start < current_timestamp) \
            .filter(WAR.war_day_end > current_timestamp).scalar()

        if war_end_time is None:
            return None
        else:
            print('make me sort descending please!')
            war_end_time = war_end_time
            hours_remaining_reminder = [3, 1]
            results = []
            for hourReminder in hours_remaining_reminder:
                this_timestamp = war_end_time - (hourReminder * 3600)
                if this_timestamp > current_timestamp:
                    time_remaining_string = '{} hours remaining in war!'.format(
                        hourReminder)
                    if hourReminder == 1:
                        time_remaining_string = '{} hour remaining in war!'.format(
                            hourReminder)
                    results.append((this_timestamp, time_remaining_string))
            if len(results) == 0:
                return None
            else:
                return results

    def get_members_in_war_with_attacks_remaining(self, clan_tag=MyConfigBot.my_clan_tag):

        current_time = DateFetcherFormatter.get_utc_timestamp()
        current_war = self.session.query(WAR) \
            .filter(WAR.friendly_tag == clan_tag) \
            .filter(WAR.war_day_start < current_time) \
            .filter(WAR.war_day_end > current_time).one_or_none()

        if current_war is None:
            raise NoActiveClanWar()
        else:
            results = {
                "discord": {},
                "no_discord": []
            }
            for war_participation in current_war.war_participations:
                member = war_participation.member

                attacks_remaining = 0
                if war_participation.attack1.stars is None:
                    attacks_remaining = 2
                elif war_participation.attack2.stars is None:
                    attacks_remaining = 1

                if attacks_remaining != 0:
                    these_results = {
                        "member_name": member.member_name,
                        "attacks_remaining": attacks_remaining
                    }
                    if len(member.discord_clash_links) == 0:
                        results["no_discord"].append(these_results)
                    for discord_clash_link in member.discord_clash_links:
                        discord_id = discord_clash_link.discord_tag
                        if discord_id not in results["discord"]:
                            results["discord"][discord_id] = []
                        results["discord"][discord_id].append(these_results)
            return results

    def link_discord_account(self, discord_identifier, clash_identifier, is_name=False):

        print(clash_identifier)
        print(is_name)

        member_query = self.session.query(MEMBER)
        if is_name:
            member_query = member_query.filter(func.upper(MEMBER.member_name) == clash_identifier)
        else:
            # tag
            member_query = member_query.filter(MEMBER.member_tag == clash_identifier)

        member_instances = member_query.all()

        if len(member_instances) == 0:
            return config_strings.unable_to_find_account_string

        if len(member_instances) > 1:
            print('Multiple accounts matched while linking, better fix this')

        member_instance = member_instances[0]

        discord_account_instance = self.session.query(DISCORDACCOUNT)\
            .filter(DISCORDACCOUNT.discord_tag == discord_identifier).one_or_none()

        if discord_account_instance is None:
            discord_account_instance = DISCORDACCOUNT()
            discord_account_instance.is_troop_donator = -1
            discord_account_instance.discord_tag = discord_identifier
            discord_account_instance.has_permission_to_set_war_status = False
            discord_account_instance.time_last_checked_in = DateFetcherFormatter.get_utc_timestamp()

        for clash_links in discord_account_instance.discord_clash_links:
            if clash_links.clash_account == member_instance:
                print('This account is already linked, should change this :)')
                return config_strings.successfully_linked_string

        discord_clash_link = DISCORDCLASHLINK()
        discord_clash_link.discord_account = discord_account_instance
        discord_clash_link.clash_account = member_instance
        discord_clash_link.account_order = len(discord_account_instance.discord_clash_links) + 1

        self.session.add(discord_account_instance)

        return config_strings.successfully_linked_string

    def has_linked_account_with_th_larger_than(self, discord_id, th_level_to_check_for):

        accounts = self.session.query(MEMBER) \
                            .join(DISCORDCLASHLINK) \
                            .filter(DISCORDCLASHLINK.discord_tag == discord_id) \
                            .filter(MEMBER.town_hall_level > th_level_to_check_for) \
                            .all()

        return len(accounts) > 0

    def has_configured_is_troop_donator(self, discord_id):

        result = self.session.query(DISCORDACCOUNT.is_troop_donator) \
                .filter(DISCORDACCOUNT.discord_tag == discord_id) \
                .one_or_none()

        if result == -1:
            return  False
        return True

    def get_members_in_clan(self, clan_tag=MyConfigBot.my_clan_tag):

        results = self.session.query(DISCORDACCOUNT) \
                                    .join(DISCORDCLASHLINK) \
                                    .join(MEMBER) \
                                    .filter(MEMBER.clan_tag == clan_tag) \
                                    .all()

        actual_results = {}

        for discord_account in results:
            is_troop_donator = 0
            if discord_account.is_troop_donator == 1:
                is_troop_donator = 1
            actual_results[str(discord_account.discord_tag)] = is_troop_donator

        return actual_results

    def get_discord_members_in_war(self):
        # find the active war day, if there is one
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.war_day_start <= current_time) \
            .filter(WAR.war_day_end >= current_time).one_or_none()

        if war_instance is None:
            # find a prep day if there is no active war day
            war_instance = self.session.query(WAR) \
                .filter(WAR.prep_day_start <= current_time) \
                .filter(WAR.war_day_start >= current_time).one_or_none()

        # if no prep day, we aren't in war at all
        if war_instance is None:
            raise NoActiveClanWar()

        war_particips = self.session.query(WARPARTICIPATION).filter(WARPARTICIPATION.war == war_instance).all()

        clash_account_numbers = set()

        for war_particip in war_particips:
            member = war_particip.member
            for discord_clash_link in member.discord_clash_links:
                clash_account_numbers.add(str(discord_clash_link.discord_tag))

        return clash_account_numbers

    def get_discord_ids_of_members_with_war_permissions(self):
        results = self.session.query(DISCORDACCOUNT) \
            .filter(DISCORDACCOUNT.has_permission_to_set_war_status == 1) \
            .all()

        actual_results = set()

        for discord_account in results:
            actual_results.add(str(discord_account.discord_tag))

        return actual_results

    def get_all_members_without_discord_as_string(self):
        result_list = self.get_all_members_without_discord()
        result_string = ""
        for entry in result_list:
            result_string += entry + '\n'
        return result_string


    def get_all_members_without_discord(self, clan_tag=MyConfigBot.my_clan_tag):

        members_in_clan = self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag).all()

        actual_results = []
        for member in members_in_clan:
            if len(member.discord_clash_links) == 0:
                actual_results.append(member.member_name)

        return actual_results

    def get_members_by_offensive_score(self, clan_tag=MyConfigBot.my_clan_tag):
        # implement this?
        all_members_in_clan = self.session.query(MEMBER).filter(MEMBER.clan_tag == clan_tag).all()

        return all_members_in_clan
        # scores = {}
        # for member in all_members_in_clan:
        #     member_score = member.town_hall_level*3
        #     member_score += member.king_level
        #     member_score += member.queen_level
        #     member_score += member.warden_level
        #     season_historical_data_instance = member.season_historical_data[-1]
        #     member_score += int(season_historical_data_instance.troops_donated / 10)
        #     member_score += season_historical_data_instance.attacks_won
        #     if member_score not in scores:
        #         scores[member_score] = []
        #     scores[member_score].append(member)
        #
        # counter = 1
        # for score in sorted(scores, reverse=True):
        #     for member in scores[score]:
        #         season_historical_data_instance = member.season_historical_data[-1]
        #         print('{}) {}:'.format(counter, member.member_name))
        #         print('    TH   : {}'.format(member.town_hall_level))
        #         print('    King : {}'.format(member.king_level))
        #         print('    Queen: {}'.format(member.queen_level))
        #         print('    GW   : {}'.format(member.warden_level))
        #         print('    Donat: {}'.format(season_historical_data_instance.troops_donated))
        #         print('    Attac: {}'.format(season_historical_data_instance.attacks_won))
        #         counter += 1
        #         pass

def getCursorAndConnection():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return cursor, conn


def getLastProcessedTime():
    cursor, conn = getCursorAndConnection()
    query = '''
	SELECT time
		FROM
			LAST_PROCESSED
		WHERE
			COUNT = 1
		'''
    cursor.execute(query)
    result = cursor.fetchone()
    if result == None:
        result = 0
    else:
        result = result[0]
    conn.close()
    return result


def getSeasonIdForTimestamp(timestamp):
    cursor, conn = getCursorAndConnection()
    query = '''
	SELECT season_id
		FROM
			SEASONS
		WHERE
			start_time <= ? and end_time >= ?
		'''
    cursor.execute(query, (timestamp, timestamp))
    result = cursor.fetchone()
    if result == None:
        result = None
    else:
        result = result[0]
    conn.close()
    return result


def getAllMembersTagSupposedlyInClan(cursor):
    cursor.execute(
        '''
		SELECT member_tag FROM
			MEMBERS
		WHERE
			in_clan_currently = 1
		'''
    )
    return cursor.fetchall()

def removeDiscordAccountsRelatedTo(accountName):
    cursor, conn = getCursorAndConnection()
    changed = 0

    query = '''SELECT discord_tag FROM discord_clash_links WHERE member_tag = (
			SELECT member_tag FROM MEMBERS WHERE UPPER(member_name) = ?
			)
		'''
    cursor.execute(query, (accountName,))
    discord_tags = cursor.fetchall()
    for discord_tag in discord_tags:
        discord_tag = discord_tag[0]
        query = '''DELETE FROM discord_clash_links WHERE discord_tag = ?'''
        cursor.execute(query, (discord_tag, ))
        changed += cursor.rowcount
        query = '''DELETE FROM discord_properties WHERE discord_tag = ?'''
        cursor.execute(query, (discord_tag, ))
        changed += cursor.rowcount
    conn.commit()
    conn.close()
    return changed


def getMembersFromLastWar():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()

    query = '''
		SELECT member_name 
		FROM
		MEMBERS where in_clan_currently = 1
		ORDER BY trophies DESC
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersList = []
    for entry in data:
        membersList.append(entry[0])

    cursor.execute(
        '''
		SELECT mems.member_name 
		FROM MEMBERS mems			
		INNER JOIN WAR_ATTACKS war_attacks
			ON war_attacks.attacker_tag = mems.member_tag
		INNER JOIN WARS wars
			ON wars.war_id = war_attacks.war_id
		WHERE
			wars.war_id = (SELECT MAX(war_id) FROM WARS)
			AND
			war_attacks.attacker_attack_number = 1
		ORDER BY mems.trophies DESC;
		'''
    )
    data = cursor.fetchall()
    conn.close()
    result = ""
    for entry in data:
        if entry[0] in membersList:
            result += str(membersList.index(entry[0]
                                            ) + 1) + ") " + entry[0] + "\n"
        else:
            result += "*X) " + entry[0] + "*\n"
    return result


def getNewWarRoster():
    try:
        val = getNewWarRoster2()
        print(val)
        return val
    except:
        print("Unexpected error:", sys.exc_info()[0])


def getNewWarRoster2():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()

    cursor, conn = getCursorAndConnection()

    query = '''
		SELECT member_name 
		FROM
		MEMBERS where in_clan_currently = 1
		ORDER BY trophies DESC
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersList = []
    for entry in data:
        membersList.append(entry[0])

    query = '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		INNER JOIN ADD_TO_WAR
			ON MEMBERS.member_tag = ADD_TO_WAR.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    membersToAdd = []
    if len(data) != 0:
        for entry in data:
            memberName = entry[0]
            if memberName in membersList:
                membersToAdd.append(memberName)

    print('adding these members to war: {}'.format(membersToAdd))

    query = '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		INNER JOIN REMOVE_FROM_WAR
			ON MEMBERS.member_tag = REMOVE_FROM_WAR.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersToRemove = []
    if len(data) != 0:
        for entry in data:
            memberName = entry[0]
            if memberName in membersList:
                membersToRemove.append(memberName)

    print('removing these members from war: {}'.format(membersToRemove))

    cursor.execute(
        '''
		SELECT mems.member_name 
		FROM MEMBERS mems			
		INNER JOIN WAR_ATTACKS war_attacks
			ON war_attacks.attacker_tag = mems.member_tag
		INNER JOIN WARS wars
			ON wars.war_id = war_attacks.war_id
		WHERE
			wars.war_id = (SELECT MAX(war_id) FROM WARS)
			AND
			war_attacks.attacker_attack_number = 1
		ORDER BY mems.trophies DESC;
		'''
    )
    data = cursor.fetchall()

    roster = []
    for entry in data:
        memberName = entry[0]
        if memberName in membersList:
            if not memberName in membersToRemove:
                roster.append(memberName)

    for memberName in membersToAdd:
        if memberName in membersList and not memberName in roster:
            roster.append(memberName)

    query = '''
		select war_size from wars where war_id = (select max(war_id) from wars)
		'''
    cursor.execute(query)
    warSize = cursor.fetchone()[0]

    print(warSize)
    origWarSize = warSize
    while len(roster) > warSize:
        warSize += 5

    while len(roster) + 5 <= warSize:
        warSize -= 5
    print(warSize)

    warSizeString = ""
    if warSize != origWarSize:
        warSizeString = "\n\nNote: changed war size from {} to {}".format(
            origWarSize, warSize)
    addedToFillString = ""

    if len(roster) < warSize:
        print('got here')
        query = '''
			SELECT MEMBERS.member_name
			FROM MEMBERS
			WHERE
				in_clan_currently = 1
			AND
				town_hall_level IS NOT NULL
			ORDER BY town_hall_level ASC
			'''
        cursor.execute(query)
        results = cursor.fetchall()
        print('results were')
        print(results)
        for result in results:
            name = result[0]
            if not name in roster:
                if addedToFillString == "":
                    addedToFillString = "\n\nNote: added these to fill roster:\n"
                print('adding to fill roster: {}'.format(name))
                addedToFillString += name + '\n'
                roster.append(name)
            if len(roster) == warSize:
                break

    result = ""
    print(len(roster))
    for i in range(0, len(membersList)):
        memberName = membersList[i]
        if memberName in roster:
            if memberName in addedToFillString:
                result += str(i+1) + ") *" + memberName + "*\n"
            else:
                result += str(i+1) + ") " + memberName + "\n"

    conn.close()
    return result + addedToFillString + warSizeString


def addMemberToWar(member_name):
    #conn = sqlite3.connect(db_file)
    # print(sqlite3.version)
    #cursor = conn.cursor()
    member_name = member_name.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		INSERT OR REPLACE INTO 
			ADD_TO_WAR (member_tag, time_requested, change_number)
		VALUES
			((SELECT member_tag from MEMBERS WHERE upper(member_name) = ?), ?, ?)
		'''
    timestamp = getDataFromServer.get_utc_timestamp()
    result = config_strings.success
    print(member_name)
    try:
        cursor.execute(query, (member_name, timestamp,
                               getMaxRosterChangeNumber(cursor, conn)+1))
    except sqlite3.IntegrityError as e:
        print(e)
        result = config_strings.failed
    conn.commit()
    conn.close()
    return result


def removeMemberFromWar(member_name):
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    member_name = member_name.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		INSERT OR REPLACE INTO 
			REMOVE_FROM_WAR (member_tag, time_requested, change_number)
		VALUES
			((SELECT member_tag from MEMBERS WHERE upper(member_name) = ?), ?, ?)
		'''
    timestamp = getDataFromServer.get_utc_timestamp()
    result = config_strings.success
    try:
        cursor.execute(query, (member_name, timestamp,
                               getMaxRosterChangeNumber(cursor, conn)+1))
    except sqlite3.IntegrityError as e:
        result = config_strings.failed
    conn.commit()
    conn.close()
    return result


def clearAddAndRemoveFromWar():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()
    query = '''
		DELETE FROM ADD_TO_WAR
		'''
    cursor.execute(query)
    query = '''
		DELETE FROM REMOVE_FROM_WAR
		'''
    cursor.execute(query)
    conn.commit()
    conn.close()


def getMaxRosterChangeNumber(cursor, conn):
    result = 0
    query = '''
		SELECT MAX(change_number) FROM ADD_TO_WAR
		'''
    cursor.execute(query)
    returnedValAdd = cursor.fetchone()[0]
    query = '''
		SELECT MAX(change_number) FROM REMOVE_FROM_WAR
		'''
    cursor.execute(query)
    returnedValRem = cursor.fetchone()[0]
    if returnedValAdd == None:
        if returnedValRem != None:
            result = returnedValRem

    if returnedValRem == None:
        if returnedValAdd != None:
            result = returnedValAdd

    if returnedValRem != None and returnedValAdd != None:
        result = max(returnedValRem, returnedValAdd)

    return result


def getPastWarPerformanceForMemberName(memberName, number_of_wars):
    memberName = memberName.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT discord_tag FROM discord_clash_links
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_clash_links.member_tag 
		WHERE
			UPPER(MEMBERS.member_name) = UPPER(?)
		'''
    cursor.execute(query, (memberName,))
    discordID = cursor.fetchall()

    print(discordID)

    if len(discordID) == 0:
        query = '''SELECT member_tag, member_name FROM members WHERE UPPER(member_name) = ?'''
        cursor.execute(query, (memberName,))
        results = cursor.fetchall()
        if len(results) == 0:
            raise ValueError('Unable to find this account')
        elif len(results) > 1:
            raise ValueError('Too many accounts with this username...')

        accounts = results[0]
        member_tag_name_dict = {}
        tag = accounts[0]
        name = accounts[1]
        member_tag_name_dict[tag] = name
        return get_past_war_performance_for_member_tags(member_tag_name_dict, number_of_wars)
    else:
        conn.close()
        if len(discordID) > 1:
            raise ValueError(
                'Too many discord ids have accounts with this username...')

        return getPastWarPerformance(discordID[0][0], number_of_wars)


def getPastWarPerformance(discord_id, number_of_wars):
    cursor, conn = getCursorAndConnection()
    # first, get all the tags and member names for every account owned by this discord id
    query = '''
		SELECT members.member_tag, members.member_name FROM MEMBERS
		INNER JOIN DISCORD_CLASH_LINKS ON
		MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
		where DISCORD_CLASH_LINKS.discord_tag = ?
		'''
    account_dict = {}
    cursor.execute(query, (int(discord_id),))
    results = cursor.fetchall()
    for account_data in results:
        tag = account_data[0]
        name = account_data[1]
        account_dict[tag] = name
    print(account_dict)
    conn.close()
    return get_past_war_performance_for_member_tags(account_dict, number_of_wars)


def get_past_war_performance_for_member_tags(member_tag_name_dict, number_of_wars):
    # get the max war id
    # determine if the current war is on going
    # go backwards until we get to the first war or to where we have the total number of desired wars
    cursor, conn = getCursorAndConnection()
    result_dict = {}
    result_dict['wars_participated_in'] = []
    query = """
	    SELECT 
                war_id, result
            FROM
                wars
            WHERE
                war_id = (SELECT MAX(war_id) FROM WARS)
	    """
    cursor.execute(query, ())
    max_war_id, result = cursor.fetchall()[0]
    if result == 'in progress':
        max_war_id = max(0, max_war_id - 1)

    where_clause = ''
    for account_tag in member_tag_name_dict:
        where_clause += "attacker_tag = ? or "
    where_clause = where_clause[:-4]
    where_clause = "(" + where_clause + ")"
    found = 0
    for war_id in range(max_war_id, 1, -1):
        #print('looping')
        query = '''SELECT war_id, attacker_tag, MEMBERS.member_name, attacker_attack_number, attacker_position, defender_position, attacker_town_hall, defender_town_hall, stars, destruction_percentage, attack_occurred_after, attack_occurred_before 
			FROM WAR_ATTACKS 
			INNER JOIN MEMBERS ON WAR_ATTACKS.attacker_tag = MEMBERS.member_tag
			WHERE war_id = ? and '''
        query += where_clause
        vars = [war_id]
        vars.extend(member_tag_name_dict.keys())
#		print(query)
#		print(vars)
        cursor.execute(query, vars)
        results = cursor.fetchall()
        if len(results) > 0:
            dict_for_this_war = {}
            dict_for_this_war['war_attacks'] = []
            for attack in results:
                dict_for_this_attack = {}
                dict_for_this_attack['member_name'] = attack[2]
                dict_for_this_attack['attack_number'] = attack[3]
                dict_for_this_attack['attacker_position'] = attack[4]
                dict_for_this_attack['defender_position'] = attack[5]
                dict_for_this_attack['attacker_town_hall'] = attack[6]
                dict_for_this_attack['defender_town_hall'] = attack[7]
                dict_for_this_attack['stars'] = attack[8]
                dict_for_this_attack['destruction_percentage'] = attack[9]
                dict_for_this_attack['attack_occurred_after'] = attack[10]
                dict_for_this_attack['attack_occurred_before'] = attack[11]
                dict_for_this_war['war_attacks'].append(dict_for_this_attack)
            query = '''SELECT result, war_day_start, war_day_end FROM WARS WHERE war_id = ?'''
            cursor.execute(query, (war_id,))
            results = cursor.fetchall()
            if len(results) != 1:
                raise ValueError(
                    'Why do there seem to be war attacks for this war but the war is not saved? War id was: {}'.format(war_id))
            war_details_dict = {}
            war_details_dict['war_id'] = war_id
            war_details_dict['result'] = results[0][0]
            war_details_dict['war_day_start'] = results[0][1]
            war_details_dict['war_day_end'] = results[0][2]
            dict_for_this_war['war_details'] = war_details_dict
            result_dict['wars_participated_in'].append(dict_for_this_war)
            found += 1
        if found >= number_of_wars:
            break
    conn.close()
    return result_dict

def getIneligibleForClanGames(thLevelRequired=6):
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT member_name, town_hall_level FROM
			MEMBERS
		WHERE
			in_clan_currently = 1
		AND
			town_hall_level < ?
		'''
    cursor.execute(query, (thLevelRequired,))
    data = cursor.fetchall()
    resultsString = "These members are ineligible for clan games:\n"
    for entry in data:
        resultsString += entry[0] + ' (TH {})'.format(entry[1]) + '\n'
    conn.close()
    return resultsString


def getAllDonatedOrReceivedInTimeFrame(time_created, time_finished):
    resultDict = {}
    resultDict['left_since_created'] = []
    resultDict['standard'] = []
    resultDict['joined_since_created'] = []
    resultDict['debug'] = [time_created, time_finished]
    time_created = time_created
    time_finished = time_finished
    cursor, conn = getCursorAndConnection()
    membersInClan = getAllMembersTagSupposedlyInClan(cursor)
    for memberTag in membersInClan:
        member_tag = memberTag[0]
        member_joined_after_request_created = False
        member_left_after_request_created = False
        max_index = get_max_index_less_than_scanned_time(cursor, time_created)
        query = '''SELECT MEMBERS.member_name, SCANNED_DATA.troops_donated_monthly, SCANNED_DATA.troops_received_monthly
			FROM
				SCANNED_DATA
			INNER JOIN MEMBERS
				ON MEMBERS.member_tag = SCANNED_DATA.member_tag
			WHERE
				SCANNED_DATA.scanned_data_index =(SELECT MAX(SCANNED_DATA.scanned_data_index) FROM SCANNED_DATA WHERE SCANNED_DATA.scanned_data_index <= ? AND SCANNED_DATA.member_tag = ?)
			AND
				SCANNED_DATA.member_tag = ?
			'''
        cursor.execute(query, (max_index, member_tag, member_tag))
        donations_before = cursor.fetchall()
        if len(donations_before) > 1:
            # throw error here
            resultDict['error'] = 'error 1'
            return resultDict
#			return 'before: {}: {}'.format(memberTag, donations_before)
        elif len(donations_before) == 0:
            member_joined_after_request_created = True
            # this is when the member just joined

        min_index = get_min_index_greater_than_scanned_time(
            cursor, time_finished)
        query = '''SELECT MEMBERS.member_name, SCANNED_DATA.troops_donated_monthly, SCANNED_DATA.troops_received_monthly
			FROM
				SCANNED_DATA
			INNER JOIN MEMBERS
				ON MEMBERS.member_tag = SCANNED_DATA.member_tag
			WHERE
				SCANNED_DATA.scanned_data_index = (SELECT MIN(SCANNED_DATA.scanned_data_index) FROM SCANNED_DATA WHERE SCANNED_DATA.scanned_data_index >= ? AND SCANNED_DATA.member_tag = ?)
			AND
				SCANNED_DATA.member_tag = ?
			'''
        cursor.execute(query, (min_index, member_tag, member_tag))
        donations_after = cursor.fetchall()
        if len(donations_after) == 0:
            member_left_after_request_created = True
        elif len(donations_after) != 1:
            # throw error here
            print(donations_after)
            resultDict['error'] = 'error 2'
            return resultDict
#			return 'after: {}: {}'.format(memberTag, donations_before)

        if member_joined_after_request_created and member_left_after_request_created:
            print('whats happening')
            resultDict['error'] = 'error 3'
            return resultDict
        elif member_joined_after_request_created:
            donated_name = donations_after[0][0]
            entry = {}
            entry['tag'] = member_tag
            entry['name'] = donated_name
            entry['donated'] = donations_after[0][1]
            entry['received'] = donations_after[0][2]
            resultDict['joined_since_created'].append(entry)
        elif member_left_after_request_created:
            donated_name = donations_before[0][0]
            entry = {}
            entry['tag'] = member_tag
            entry['name'] = donated_name
            entry['donated'] = '?'
            entry['received'] = '?'
            resultDict['left_since_created'].append(entry)
        else:
            donated_name = donations_before[0][0]

            donated_before_num = donations_before[0][1]
            donated_after_num = donations_after[0][1]
            donated = donated_after_num - donated_before_num

            received_before_num = donations_before[0][2]
            received_after_num = donations_after[0][2]
            received = received_after_num - received_before_num

            if donated != 0 or received != 0:
                entry = {}
                entry['tag'] = member_tag
                entry['name'] = donated_name
                entry['donated'] = donated
                entry['received'] = received
                resultDict['standard'].append(entry)

    conn.close()
    return resultDict


def getMembersWithScoreUnderThreshold(threshold, extraRequiredPerAccount=200):
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()

    cursor.execute('SELECT MAX (clan_games_id) FROM CLAN_GAMES_SCORE')
    maxClanGamesID = cursor.fetchone()[0]
    data = []
#	ineligible = []
    for i in range(maxClanGamesID-4, maxClanGamesID+1):
        print('looping')

        cursor.execute(
            '''
			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
			FROM MEMBERS mems
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
			WHERE
				mems.town_hall_level >= (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_id = ?)
			AND
				CLAN_GAMES_SCORE.clan_games_id = ?
			AND
				mems.in_clan_currently = 1
			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_id;
			''', (i, i,)
        )
        results = cursor.fetchall()
        print(results)
        print(i)
        data.extend(results)
#		cursor.execute(
#			'''
#			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
#			FROM MEMBERS mems
#			INNER JOIN CLAN_GAMES_SCORE
#				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
#			WHERE
#				mems.town_hall_level < (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_id = ?)
#			AND
#				CLAN_GAMES_SCORE.clan_games_id = ?
#			AND
#				mems.in_clan_currently = 1
#			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_id;
#			'''
#			,(i,i,)
#			)
#		ineligible.extend(cursor.fetchall())

    combinedScores = {}
    membersThatAreTooLow = []

    for entry in data:
        clanGamesID = entry[2]
        name = entry[0]
        tag = entry[1]
        score = entry[3]
        query = '''
			SELECT discord_tag FROM DISCORD_CLASH_LINKS
			WHERE 
				member_tag = ?
			'''
        cursor.execute(query, (tag,))
        discordTag = cursor.fetchone()
        if discordTag == None:
            print('{} has no discord'.format(name))
            if score <= threshold:
                membersThatAreTooLow.append((name, clanGamesID, score))
        else:
            print('{} has a discord'.format(name))
            discordTag = discordTag[0]
            query = '''
				
				'''

            if not discordTag in combinedScores:
                combinedScores[discordTag] = {}
                combinedScores[discordTag]['name'] = set()
                combinedScores[discordTag]['GamesList'] = {}
            combinedScores[discordTag]['name'].add(name)
            if clanGamesID not in combinedScores[discordTag]['GamesList']:
                combinedScores[discordTag]['GamesList'][clanGamesID] = 0
            combinedScores[discordTag]['GamesList'][clanGamesID] += score

    print(combinedScores)

    for discordTag in combinedScores:
        gamesList = combinedScores[discordTag]['GamesList']
        for clanGameID in gamesList:
            if gamesList[clanGameID] <= threshold + extraRequiredPerAccount*(len(combinedScores[discordTag]['name'])-1):
                names = combinedScores[discordTag]['name']
                name = ""
                for nameInd in names:
                    name += nameInd + "/"
                name = name[:-1]
                membersThatAreTooLow.append(
                    ((name, clanGameID, gamesList[clanGameID])))
                print('{} was below threshold'.format(name))
            else:
                print(combinedScores[discordTag]['name'])
                print('was above threshold')

    result = ""
    prevID = None

    conn.close()

    membersThatAreTooLow = sorted(membersThatAreTooLow, key=lambda x: x[0])

    for entry in membersThatAreTooLow:
        print(entry)
        result += str(entry[1]) + ") " + entry[0] + ' ' + str(entry[2]) + "\n"
    print(result)
    return result

def getAllLinkedAccountsList():
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT MEMBERS.member_name, DISCORD_CLASH_LINKS.discord_tag
		FROM MEMBERS
		INNER JOIN 
		DISCORD_CLASH_LINKS ON
		DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    conn.close()
    accounts = {}
    for entry in data:
        name = entry[0]
        discordTag = entry[1]
        if not discordTag in accounts:
            accounts[discordTag] = []
        accounts[discordTag].append(name)
    resultString = ""
    for id in accounts:
        for name in accounts[id]:
            resultString += name + '\n'
        resultString += '\n'
    return resultString


def getLinkedAccountsList(discordID, currently_in_clan_required=False):
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT MEMBERS.member_name
		FROM 
			MEMBERS
		INNER JOIN DISCORD_CLASH_LINKS
			ON DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
		WHERE
			DISCORD_CLASH_LINKS.discord_tag = ?		
		'''
    if currently_in_clan_required:
        query += " AND MEMBERS.in_clan_currently = 1"
    query += " ORDER BY DISCORD_CLASH_LINKS.account_order"

    cursor.execute(query, (discordID,))
    accountResults = cursor.fetchall()

    query = '''
		UPDATE DISCORD_PROPERTIES SET time_last_checked_in = ?
		WHERE
			discord_tag = ?
		'''
    cursor.execute(query, (getDataFromServer.get_utc_timestamp(), discordID,))

    for i in range(0, len(accountResults)):
        accountResults[i] = accountResults[i][0]

    conn.commit()
    conn.close()
    return accountResults


def getLinkedAccounts(discordID):
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    # need to fetch and print
    accountResults = getLinkedAccountsList(discordID)
    if len(accountResults) == 0:
        result = "You own 0 accounts. Please link yours!"
    else:
        result = "You own {} accounts:\n".format(len(accountResults))
        for account in accountResults:
            result += "{}\n".format(account)
    return result


def getRosterChanges():
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT ADD_TO_WAR.change_number, MEMBERS.member_name 
		FROM 
			MEMBERS
		INNER JOIN ADD_TO_WAR
			ON ADD_TO_WAR.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    addedToWar = cursor.fetchall()
    query = '''
		SELECT REMOVE_FROM_WAR.change_number, MEMBERS.member_name 
		FROM 
			MEMBERS
		INNER JOIN REMOVE_FROM_WAR
			ON REMOVE_FROM_WAR.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    removedFromWar = cursor.fetchall()
    conn.commit()
    conn.close()

    addedString = "No members being added to war.\n"
    if len(addedToWar) > 0:
        addedString = "These members will be added to war.\n"
        for account in addedToWar:
            addedString += '{}) {}\n'.format(account[0], account[1])

    removedString = "No members being removed from war.\n"
    if len(removedFromWar) > 0:
        removedString = "These members will be removed from war.\n"
        for account in removedFromWar:
            removedString += '{}) {}\n'.format(account[0], account[1])

    return addedString + removedString


def undoWarChange(changeNumber):
    changed = 0
    cursor, conn = getCursorAndConnection()
    query = '''
		DELETE FROM add_to_war 
		WHERE
		change_number = ?
		'''
    cursor.execute(query, (changeNumber,))
    changed += cursor.rowcount
    query = '''
		DELETE FROM remove_from_war 
		WHERE
		change_number = ?
		'''
    cursor.execute(query, (changeNumber,))
    changed += cursor.rowcount
    conn.commit()
    conn.close()
    return changed


def getClanGamesResultsForMemberName(memberName):
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT discord_tag FROM discord_clash_links
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_clash_links.member_tag 
		WHERE
			UPPER(MEMBERS.member_name) = UPPER(?)
		'''
    cursor.execute(query, (memberName,))
    discordID = cursor.fetchone()

    if discordID is None:
        query = '''
			SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
			FROM MEMBERS			
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
			WHERE
				UPPER(MEMBERS.member_name) = UPPER(?)
			ORDER BY CLAN_GAMES_SCORE.clan_games_id, MEMBERS.member_name
			'''
        cursor.execute(query, (memberName,))
        results = cursor.fetchall()

        resultsString = "Unable to find this account\n"

        if len(results) > 0:
            resultsString = "Here are your results:\n"
            previousClanGames = None
            for result in results:
                cgNumber = result[1]
                name = result[0]
                score = result[2]
                if result[1] != previousClanGames:
                    previousClanGames = result[1]
                    resultsString += '\n**Clan games \#{}:\n**'.format(
                        cgNumber)
                resultsString += '{} scored: {}\n'.format(name, score)
        return resultsString
    else:
        conn.close()
        return getClanGamesResultsFor(discordID[0])


def getClanGamesResultsFor(discordID):
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
		FROM MEMBERS			
		INNER JOIN CLAN_GAMES_SCORE
			ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
		INNER JOIN DISCORD_CLASH_LINKS
			ON DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
		WHERE
			DISCORD_CLASH_LINKS.discord_tag = ?
		ORDER BY CLAN_GAMES_SCORE.clan_games_id, DISCORD_CLASH_LINKS.account_order, MEMBERS.member_name
		''', (discordID,))
    results = cursor.fetchall()

    resultsString = "Here are your results:\n"

    if len(results) > 0:
        previousClanGames = None
        for result in results:
            cgNumber = result[1]
            name = result[0]
            score = result[2]
            if result[1] != previousClanGames:
                previousClanGames = result[1]
                resultsString += '\n**Clan games \#{}:\n**'.format(cgNumber)
            resultsString += '{} scored: {}\n'.format(name, score)

    return resultsString


def checkTroopDonator(discordID, valExpected):
    result = False
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT is_troop_donator
		FROM DISCORD_PROPERTIES
		WHERE discord_tag = ?
		'''
    cursor.execute(query, (discordID,))
    answer = cursor.fetchone()
    if answer != None:
        answer = answer[0]
        if answer == valExpected:
            result = True
    return result


def setTroopDonator(discordID, val):
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		UPDATE DISCORD_PROPERTIES
		SET is_troop_donator = ?
		WHERE discord_tag = ?
		''',
        (val, discordID)
    )

    result = cursor.rowcount
    conn.commit()
    conn.close()
    return result

def getMembersInWarWithoutDiscordAsString():
    resultList = getMembersInWarWithoutDiscord()
    resultString = ""
    for entry in resultList:
        resultString += entry + '\n'
    return resultString


def getMembersInWarWithoutDiscord():
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		WHERE 
			MEMBERS.in_war_currently = 1

		AND MEMBERS.member_name NOT IN
			(
				SELECT MEMBERS.member_name
				FROM MEMBERS
				INNER JOIN DISCORD_CLASH_LINKS
					ON MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
				WHERE
					MEMBERS.in_war_currently = 1
			)
		'''
    )
    results = cursor.fetchall()
    conn.close()
    actualResults = []

    for result in results:
        actualResults.append(result[0])

    return actualResults

def getAccountsWhoGetGiftReminders(currentDateTime):
    # discordID, accountName, ensure they're in the clan still and wants to get notifications
    cursor, conn = getCursorAndConnection()
    currentWeekDay = currentDateTime.weekday()
    currentHour = currentDateTime.hour
    query = '''
			SELECT MEMBERS.member_name, DISCORD_CLASH_LINKS.discord_tag
			FROM MEMBERS
			INNER JOIN DISCORD_CLASH_LINKS
			ON
				DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
			WHERE
				MEMBERS.in_clan_currently = 1
			AND
				MEMBERS.free_item_day_of_week = ?
			AND
				MEMBERS.free_item_hour_to_remind = ?
			AND
				MEMBERS.wants_gift_reminder = ?
			'''
    cursor.execute(query, (currentWeekDay, currentHour, 1))
    results = cursor.fetchall()
    conn.close()

    prettyData = []
    for entry in results:
        prettyEntry = {}
        prettyEntry['accountName'] = entry[0]
        prettyEntry['discord'] = entry[1]
        prettyData.append(prettyEntry)

    return prettyData


def setMemberFreeGiftDayAndTime(memberName, dayOfWeek, hourToRemindAt, discordID):
    cursor, conn = getCursorAndConnection()
    query = '''
		UPDATE MEMBERS
		SET
			free_item_day_of_week = ?,
			free_item_hour_to_remind = ?,
			wants_gift_reminder = ?
		WHERE
			member_name = ?
		AND
			member_tag in (SELECT member_tag FROM DISCORD_CLASH_LINKS WHERE discord_tag = ?)
		'''
    print(memberName)
    print(discordID)
    result = config_strings.success
    try:
        cursor.execute(query, (dayOfWeek, hourToRemindAt,
                               1, memberName, discordID))
    except Exception as e:
        print(e)
        result = config_strings.failed
    if cursor.rowcount != 1:
        result = config_strings.failed
    conn.commit()
    conn.close()
    return result


def getDiscordIDForAccountName(accountName):
    cursor, conn = getCursorAndConnection()
    query = '''SELECT DISCORD_CLASH_LINKS.discord_tag
		FROM DISCORD_CLASH_LINKS
		INNER JOIN MEMBERS
		ON MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
		WHERE UPPER(member_name) = ?
		'''
    cursor.execute(query, (accountName, ))
    results = cursor.fetchall()
    conn.close()
    return results


def setWarPermissionVal(memberName, val):
    discordID = 'somebs'
    discordIDRaw = getDiscordIDForAccountName(memberName)
    if len(discordIDRaw) > 0:
        discordID = discordIDRaw[0][0]
    cursor, conn = getCursorAndConnection()
    query = '''UPDATE DISCORD_PROPERTIES 
			SET has_permission_to_set_war_status = ? 
			WHERE discord_tag = ?
		'''

    cursor.execute(query, (val, discordID))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    return rowcount


def verifyAccountExists(memberName):
    memberName = memberName.upper()
    cursor, conn = getCursorAndConnection()
    query = '''SELECT * FROM MEMBERS WHERE UPPER(member_name) = ?'''
    cursor.execute(query, (memberName,))
    results = cursor.fetchall()
    conn.close()
    return len(results)


def getMembersWithPoorWarPerformance():
    cursor, conn = getCursorAndConnection()
    query = '''
            SELECT 
                member_tag, member_name 
            FROM
                members
            WHERE
                in_clan_currently = 1
            '''
    cursor.execute(query)
    results = cursor.fetchall()
    if len(results) == 0:
        return None

    num_wars_to_go_back = 5

    war_size_query = 'SELECT war_id, war_size FROM wars'
    cursor.execute(war_size_query)
    war_size_results = cursor.fetchall()
    war_size_dict = {war_id:war_size for (war_id, war_size) in war_size_results}

    # this is hacky but as I am in the middle of a rewrite this branch shouldn't
    # be used too long so ignore the ugly :)
    for entry in results:
        tag, name = entry
        member_tags = {tag:name}
        results = get_past_war_performance_for_member_tags(member_tags, num_wars_to_go_back)
        member_attacks_count = 0
        attack_deviations = []
        missed = 0
        zero_star = 0
        one_star = 0
        two_star = 0
        three_star = 0
        member_attacks_count_made = 0
        for entry in results['wars_participated_in']:
            #member_attacks.extend(entry['war_attacks'])
            this_war_id = entry['war_details']['war_id']
            this_war_size = war_size_dict[this_war_id]
            for attack in entry['war_attacks']:
                member_attacks_count += 1
                if attack['defender_town_hall'] == None:
                    missed += 1
                    continue
                elif attack['stars'] == 0:
                    zero_star += 1
                elif attack['stars'] == 1:
                    one_star += 1
                elif attack['stars'] == 2:
                    two_star += 1
                elif attack['stars'] == 3:
                    three_star += 1
                member_attacks_count_made += 1
                attacker_position_on_map = attack['attacker_position']
                defender_position_on_map = attack['defender_position']
                deviation = 100 * (attacker_position_on_map - defender_position_on_map) / this_war_size
                deviation = '{:.2f}'.format(deviation)
                attack_deviations.append(deviation)
#                print('attacker pos: {}'.format(attacker_position_on_map))
#                print('defender pos: {}'.format(defender_position_on_map))
#                print('dev: {}'.format(deviation))
        total_attacks = member_attacks_count
        if total_attacks == 0:
            percent_zero_star = '-'
            percent_one_star = '-'
            percent_two_star = '-'
            percent_three_star = '-'
            percent_no_show = '-'
        elif member_attacks_count_made == 0:
            percent_zero_star = '-'
            percent_one_star = '-'
            percent_two_star = '-'
            percent_three_star = '-'
            percent_no_show = '100'
        else:
            percent_zero_star = '{:.2f}'.format(100 * zero_star / member_attacks_count_made)
            percent_one_star = '{:.2f}'.format(100 * one_star / member_attacks_count_made)
            percent_two_star = '{:.2f}'.format(100 * two_star / member_attacks_count_made)
            percent_three_star = '{:.2f}'.format(100 * three_star / member_attacks_count_made)
            percent_no_show = '{:.2f}'.format(100 * missed / total_attacks)
            
        th_query = 'SELECT town_hall_level FROM members WHERE member_tag = ?'
        cursor.execute(th_query, (tag,))
        current_th = cursor.fetchall()[0][0]

        print(name)
        print('Current town hall: {}'.format(current_th))
        print('Number of attacks possible: {}'.format(member_attacks_count))
        print('Percentage no show: {}%'.format(percent_no_show))
        print('Number of attacks made: {}'.format(member_attacks_count_made))
        print('Percentage 3*: {}%'.format(percent_three_star))
        print('Percentage 2*: {}%'.format(percent_two_star))
        print('Percentage 1*: {}%'.format(percent_one_star))
        print('Percentage 0*: {}%'.format(percent_zero_star))
        print('Attack deviations: {}%'.format(attack_deviations))
        #print(member_attacks)
        print('')
    conn.close()

if __name__ == "__main__":
    #	result = getMembersFromLastWar()
    #result = getMembersWithScoreUnderThreshold(300)
    #print(result)
    # getMembersWithPoorWarPerformance()
    print("I'm running but have no tasks")
