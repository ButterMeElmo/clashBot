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
import getDataFromServer
import config_strings

db_file = "clashData.db"
#currentSeasonIDs = {}

class NoDataDuringTimeSpanException(Exception):
	pass

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
	SELECT season_ID
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

def get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, min_timestamp, max_timestamp):
	if min_timestamp > 1995812705:
		raise ValueError('Invalid timestamp, should not be milliseconds')
	if max_timestamp > 1995812705:
		raise ValueError('Invalid timestamp, should not be milliseconds')
	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time > ? and time < ?'''
	cursor.execute(query, (min_timestamp, max_timestamp))
	results = cursor.fetchall()
	if len(results) == 0:
		raise NoDataDuringTimeSpanException()
	else:
		min_index = min(results, key = lambda t:t[0])[0]
		max_index = max(results, key = lambda t:t[0])[0]
	return min_index, max_index

def get_min_index_greater_than_scanned_time(cursor, min_timestamp):
	if min_timestamp > 1995812705:
		raise ValueError('Invalid timestamp, should not be milliseconds')
	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time > ?'''
	cursor.execute(query, (min_timestamp,))
	results = cursor.fetchall()
	if len(results) == 0:
		raise NoDataDuringTimeSpanException()
	else:
		min_index = min(results, key = lambda t:t[0])[0]
	return min_index

def get_max_index_less_than_scanned_time(cursor, max_timestamp):
	if max_timestamp > 1995812705:
		raise ValueError('Invalid timestamp, should not be milliseconds')
	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time < ?'''
	cursor.execute(query, (max_timestamp,))
	results = cursor.fetchall()
	if len(results) == 0:
		raise NoDataDuringTimeSpanException()
	else:
		max_index = max(results, key = lambda t:t[0])[0]
	return max_index

def removeDiscordAccountsRelatedTo(accountName):
	cursor, conn = getCursorAndConnection()
	changed = 0

	query = '''SELECT discord_tag FROM discord_names WHERE member_tag = (
			SELECT member_tag FROM MEMBERS WHERE UPPER(member_name) = ?
			)
		'''
	cursor.execute(query, (accountName,))
	discord_tags = cursor.fetchall()
	for discord_tag in discord_tags:
		discord_tag = discord_tag[0]
		query = '''DELETE FROM discord_names WHERE discord_tag = ?'''
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
			result +=  str(membersList.index(entry[0]) + 1) + ") " + entry[0] + "\n"
		else:			
			result +=  "*X) " + entry[0] + "*\n"
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
		warSizeString = "\n\nNote: changed war size from {} to {}".format(origWarSize, warSize)
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
			result += str(i+1) + ") " + memberName + "\n"		
		
	conn.close()
	return result + addedToFillString + warSizeString

def addMemberToWar(member_name):
	#conn = sqlite3.connect(db_file)	
	#print(sqlite3.version)
	#cursor = conn.cursor()
	member_name = member_name.upper()
	cursor, conn = getCursorAndConnection()
	query = '''
		INSERT OR REPLACE INTO 
			ADD_TO_WAR (member_tag, time_requested, change_number)
		VALUES
			((SELECT member_tag from MEMBERS WHERE upper(member_name) = ?), ?, ?)
		'''
	timestamp = getDataFromServer.getUTCTimestamp()
	result = config_strings.success
	print(member_name)
	try:
		cursor.execute(query, (member_name, timestamp, getMaxRosterChangeNumber(cursor, conn)+1))
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
	timestamp = getDataFromServer.getUTCTimestamp()
	result = config_strings.success
	try:
		cursor.execute(query, (member_name, timestamp, getMaxRosterChangeNumber(cursor, conn)+1))
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
		SELECT discord_tag FROM discord_names
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_names.member_tag 
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
			raise ValueError('Too many discord ids have accounts with this username...')
				
		return getPastWarPerformance(discordID[0][0], number_of_wars)


def getPastWarPerformance(discord_id, number_of_wars):
	cursor, conn = getCursorAndConnection()
	# first, get all the tags and member names for every account owned by this discord id
	query = '''
		SELECT members.member_tag, members.member_name FROM MEMBERS
		INNER JOIN DISCORD_NAMES ON
		MEMBERS.member_tag = DISCORD_NAMES.member_tag
		where DISCORD_NAMES.discord_tag = ?
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
	result_dict['recent_wars_fought_in'] = []
	query = """
		SELECT MAX(war_id) FROM WARS
		"""
	cursor.execute(query, ())
	max_war_id = cursor.fetchall()[0][0]

	where_clause = ''
	for account_tag in member_tag_name_dict:
		where_clause += "attacker_tag = ? or "
	where_clause = where_clause[:-4]
	where_clause = "(" + where_clause + ")"
	found = 0
	for i in range(max_war_id, 1, -1):
		print('looping')
		query = '''SELECT war_id, attacker_tag, attacker_attack_number, attacker_position, defender_position, attacker_town_hall, defender_town_hall, stars, destruction_percentage FROM WAR_ATTACKS WHERE war_id = ? and '''
		query += where_clause
		vars = [ i ]
		vars.extend(member_tag_name_dict.keys())
		print(query)
		print(vars)
		cursor.execute(query, vars)
		results = cursor.fetchall()
		dict_for_this_war = results
		result_dict[i] = dict_for_this_war
		if len(results) > 0:
			found += 1
		if found >= number_of_wars:
			break
	conn.close()
	return result_dict
	

def linkDiscordAccount(discordIdentifier, clashIdentifier, isName = False):
#	conn = sqlite3.connect(db_file)	
#	print(sqlite3.version)
#	cursor = conn.cursor()
	cursor, conn = getCursorAndConnection()
	result = "An unexpected error occurred!"

	query = '''
		INSERT OR REPLACE INTO
			DISCORD_PROPERTIES (discord_tag, is_troop_donator, has_permission_to_set_war_status, time_last_checked_in)
		VALUES
			(
				?, 
				COALESCE((SELECT is_troop_donator FROM DISCORD_PROPERTIES WHERE discord_tag = ?), -1),
				COALESCE((SELECT has_permission_to_set_war_status FROM DISCORD_PROPERTIES WHERE discord_tag = ?), 0),				
				?
			)
		'''
	cursor.execute(query, (discordIdentifier, discordIdentifier, discordIdentifier, 0))

	if isName:
		query = '''
			INSERT OR REPLACE INTO
				DISCORD_NAMES (member_tag, discord_tag, account_order)
			VALUES
				(
					(SELECT member_tag FROM MEMBERS WHERE UPPER(member_name) = ?), 
					?,
					COALESCE((SELECT account_order FROM DISCORD_NAMES where member_tag = (SELECT member_tag FROM MEMBERS WHERE UPPER(member_name) = ?)), ?)
				)
			'''
	else:
		query = '''
			INSERT OR REPLACE INTO
				DISCORD_NAMES (member_tag, discord_tag, account_order)
			VALUES
				(
					?, 
					?,
					COALESCE((SELECT account_order FROM DISCORD_NAMES where member_tag = ?), ?)
				)
			'''
	try:
		cursor.execute('SELECT MAX(account_order) FROM DISCORD_NAMES WHERE discord_tag = ?', (discordIdentifier,))
		results = cursor.fetchone()[0]
		maxNum = 0
		if not results == None:
			maxNum = results
		cursor.execute(query, (clashIdentifier, discordIdentifier, clashIdentifier, maxNum+1))
	except sqlite3.IntegrityError as e:
		result = config_strings.unable_to_find_account_string
	rowCount = cursor.rowcount
	conn.commit()
	conn.close()
	if rowCount == 1:
		result = config_strings.successfully_linked_string
	return result

def getIneligibleForClanGames(thLevelRequired = 6):
	cursor, conn = getCursorAndConnection()
	query = '''
		SELECT member_name, town_hall_level FROM
			MEMBERS
		WHERE
			in_clan_currently = 1
		AND
			town_hall_level < ?
		'''
	cursor.execute(query,(thLevelRequired,))
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
	time_created = time_created * 1000
	time_finished = time_finished * 1000
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

		min_index = get_min_index_greater_than_scanned_time(cursor, time_finished)
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

def getMembersWithScoreUnderThreshold(threshold, extraRequiredPerAccount = 200):
#	conn = sqlite3.connect(db_file)	
#	print(sqlite3.version)
#	cursor = conn.cursor()
	cursor, conn = getCursorAndConnection()
	
	cursor.execute('SELECT MAX (clan_games_ID) FROM CLAN_GAMES_SCORE')
	maxClanGamesID = cursor.fetchone()[0]
	data = []
#	ineligible = []
	for i in range(maxClanGamesID-4, maxClanGamesID+1):
		print('looping')

		cursor.execute(
			'''
			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_ID, CLAN_GAMES_SCORE.score
			FROM MEMBERS mems
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
			WHERE
				mems.town_hall_level >= (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_ID = ?)
			AND
				CLAN_GAMES_SCORE.clan_games_ID = ?
			AND
				mems.in_clan_currently = 1
			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_ID;
			'''
			,(i,i,)
			)
		results = cursor.fetchall()
		print(results)
		print(i)
		data.extend(results)
#		cursor.execute(
#			'''
#			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_ID, CLAN_GAMES_SCORE.score
#			FROM MEMBERS mems
#			INNER JOIN CLAN_GAMES_SCORE
#				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
#			WHERE
#				mems.town_hall_level < (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_ID = ?)
#			AND
#				CLAN_GAMES_SCORE.clan_games_ID = ?
#			AND
#				mems.in_clan_currently = 1
#			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_ID;
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
			SELECT discord_tag FROM DISCORD_NAMES
			WHERE 
				member_tag = ?
			'''
		cursor.execute(query, (tag,))
		discordTag = cursor.fetchone()
		if discordTag == None:
			print('{} has no discord'.format(name))
			if score <=  threshold:
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
				membersThatAreTooLow.append(((name, clanGameID, gamesList[clanGameID])))
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

def hasLinkedAccountWithTHLargerThan(discordID, thLevelToCheckFor):
	cursor, conn = getCursorAndConnection()
	query = '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		INNER JOIN 
		DISCORD_NAMES ON
		DISCORD_NAMES.member_tag = MEMBERS.member_tag
		WHERE
		MEMBERS.town_hall_level >= ?
		AND
		DISCORD_NAMES.discord_tag = ?
		'''
	cursor.execute(query, (thLevelToCheckFor, discordID))
	results = cursor.fetchall()
	if len(results) > 0:
		return True
	return False

def hasConfiguredIsTroopDonator(discordID):
	cursor, conn = getCursorAndConnection()
	query = '''
		SELECT is_troop_donator
		FROM 
		DISCORD_PROPERTIES
		WHERE
		discord_tag = ?
		'''
	cursor.execute(query, (discordID,))
	result = cursor.fetchone()[0]
	if result == -1:
		# not configured yet
		return False
	return True

def getAllLinkedAccountsList():
	cursor, conn = getCursorAndConnection()
	query = '''
		SELECT MEMBERS.member_name, DISCORD_NAMES.discord_tag
		FROM MEMBERS
		INNER JOIN 
		DISCORD_NAMES ON
		DISCORD_NAMES.member_tag = MEMBERS.member_tag
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

def getLinkedAccountsList(discordID, currently_in_clan_required = False):
	cursor, conn = getCursorAndConnection()
	query = '''
		SELECT MEMBERS.member_name
		FROM 
			MEMBERS
		INNER JOIN DISCORD_NAMES
			ON DISCORD_NAMES.member_tag = MEMBERS.member_tag
		WHERE
			DISCORD_NAMES.discord_tag = ?		
		'''
	if currently_in_clan_required:
		query += " AND MEMBERS.in_clan_currently = 1"
	query += " ORDER BY DISCORD_NAMES.account_order"

	cursor.execute(query, (discordID,))
	accountResults = cursor.fetchall()

	query = '''
		UPDATE DISCORD_PROPERTIES SET time_last_checked_in = ?
		WHERE
			discord_tag = ?
		'''
	cursor.execute(query, (getDataFromServer.getUTCTimestamp(), discordID, ))


	for i in range(0,len(accountResults)):
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
		SELECT discord_tag FROM discord_names
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_names.member_tag 
		WHERE
			UPPER(MEMBERS.member_name) = UPPER(?)
		'''
	cursor.execute(query, (memberName,))
	discordID = cursor.fetchone()

	if discordID is None:
		query = '''
			SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_ID, CLAN_GAMES_SCORE.score
			FROM MEMBERS			
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
			WHERE
				UPPER(MEMBERS.member_name) = UPPER(?)
			ORDER BY CLAN_GAMES_SCORE.clan_games_ID, MEMBERS.member_name
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
					resultsString += '\n**Clan games \#{}:\n**'.format(cgNumber)
				resultsString += '{} scored: {}\n'.format(name, score)
		return resultsString
	else:
		conn.close()
		return getClanGamesResultsFor(discordID[0])
	
def getClanGamesResultsFor(discordID):
	cursor, conn = getCursorAndConnection()
	cursor.execute(
		'''
		SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_ID, CLAN_GAMES_SCORE.score
		FROM MEMBERS			
		INNER JOIN CLAN_GAMES_SCORE
			ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
		INNER JOIN DISCORD_NAMES
			ON DISCORD_NAMES.member_tag = MEMBERS.member_tag
		WHERE
			DISCORD_NAMES.discord_tag = ?
		ORDER BY CLAN_GAMES_SCORE.clan_games_ID, DISCORD_NAMES.account_order, MEMBERS.member_name
		'''
		, (discordID,))
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
		'''
		,
		(val, discordID)
		)

	result = cursor.rowcount
	conn.commit()
	conn.close()
	return result

def getMembersInClan():
	cursor, conn = getCursorAndConnection()
	cursor.execute(
		'''
		SELECT DISCORD_NAMES.discord_tag, DISCORD_PROPERTIES.is_troop_donator
		FROM DISCORD_NAMES
		INNER JOIN MEMBERS
			ON DISCORD_NAMES.member_tag = MEMBERS.member_tag
		INNER JOIN DISCORD_PROPERTIES
			ON DISCORD_NAMES.discord_tag = DISCORD_PROPERTIES.discord_tag
		WHERE
			MEMBERS.in_clan_currently = 1
		'''
		)
	results = cursor.fetchall()

	actualResults = {}

	for result in results:
		isTroopDonator = False
		if result[1]:
			isTroopDonator = True
		actualResults[str(result[0])] = isTroopDonator

	return actualResults


def getDiscordMembersInWar():
	cursor, conn = getCursorAndConnection()
	cursor.execute(
		'''
		SELECT DISCORD_NAMES.discord_tag
		FROM DISCORD_NAMES
		INNER JOIN MEMBERS
			ON DISCORD_NAMES.member_tag = MEMBERS.member_tag
		WHERE
			MEMBERS.in_war_currently = 1
		'''
		)
	results = cursor.fetchall()
	conn.close()
	actualResults = set()

	for result in results:
		actualResults.add(str(result[0]))

	return actualResults

def getDiscordIDsOfMembersWithWarPermissions():
	cursor, conn = getCursorAndConnection()
	cursor.execute(
		'''
		SELECT discord_tag
		FROM DISCORD_PROPERTIES
		WHERE
			has_permission_to_set_war_status = 1
		'''
		)
	results = cursor.fetchall()
	conn.close()
	actualResults = set()

	for result in results:
		actualResults.add(str(result[0]))

	return actualResults

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
				INNER JOIN DISCORD_NAMES
					ON MEMBERS.member_tag = DISCORD_NAMES.member_tag
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

def getAllMembersWithoutDiscordAsString():
	resultList = getAllMembersWithoutDiscord()
	resultString = ""
	for entry in resultList:
		resultString += entry + '\n'
	return resultString

def getAllMembersWithoutDiscord():
	cursor, conn = getCursorAndConnection()
	cursor.execute(
		'''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		WHERE 
			MEMBERS.in_clan_currently = 1

		AND MEMBERS.member_name NOT IN
			(
				SELECT MEMBERS.member_name
				FROM MEMBERS
				INNER JOIN DISCORD_NAMES
					ON MEMBERS.member_tag = DISCORD_NAMES.member_tag
				WHERE
					MEMBERS.in_clan_currently = 1
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
	#discordID, accountName, ensure they're in the clan still and wants to get notifications
	cursor, conn = getCursorAndConnection()
	currentWeekDay = currentDateTime.weekday()
	currentHour = currentDateTime.hour
	query = '''
			SELECT MEMBERS.member_name, DISCORD_NAMES.discord_tag
			FROM MEMBERS
			INNER JOIN DISCORD_NAMES
			ON
				DISCORD_NAMES.member_tag = MEMBERS.member_tag
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
	query =	'''
		UPDATE MEMBERS
		SET
			free_item_day_of_week = ?,
			free_item_hour_to_remind = ?,
			wants_gift_reminder = ?
		WHERE
			member_name = ?
		AND
			member_tag in (SELECT member_tag FROM DISCORD_NAMES WHERE discord_tag = ?)
		'''
	print(memberName)
	print(discordID)
	result = config_strings.success
	try:
		cursor.execute(query, (dayOfWeek, hourToRemindAt, 1, memberName, discordID))
	except Exception as e:
		print(e)
		result = config_strings.failed
	if cursor.rowcount != 1:
		result = config_strings.failed
	conn.commit()
	conn.close()
	return result

def getTimestampsForCurrentWar():
	currentWarID = None
	currentTimestamp = getDataFromServer.getUTCTimestamp()
	cursor, conn = getCursorAndConnection()
	query = '''
			SELECT war_day_end FROM WARS
			WHERE war_day_end > ?
			'''
	cursor.execute(query, (currentTimestamp,))
	warEndTime = cursor.fetchone()
	if warEndTime == None:
		return None
	else:
		print('make me sort descending please!')
		warEndTime = warEndTime[0]
		hoursRemainingReminder = [3, 1]
		results = []
		for hourReminder in hoursRemainingReminder:
			thisTimestamp =  warEndTime - (hourReminder * 3600)
			if thisTimestamp > currentTimestamp:
				results.append(thisTimestamp)
		if len(results) == 0:
			return None
		else:
			return results

def getDiscordIDForAccountName(accountName):
	cursor, conn = getCursorAndConnection()
	query = '''SELECT DISCORD_NAMES.discord_tag
		FROM DISCORD_NAMES
		INNER JOIN MEMBERS
		ON MEMBERS.member_tag = DISCORD_NAMES.member_tag
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

def getMembersInWarWithAttacksRemaining():
	cursor, conn = getCursorAndConnection()
	query = '''
			SELECT MEMBERS.member_name, DISCORD_NAMES.discord_tag
			FROM MEMBERS
			INNER JOIN WAR_ATTACKS 
			ON WAR_ATTACKS.attacker_tag = MEMBERS.member_tag
			INNER JOIN DISCORD_NAMES
			ON DISCORD_NAMES.member_tag = MEMBERS.member_tag
			WHERE 
				WAR_ATTACKS.war_id = (SELECT MAX(war_id) FROM WARS)
			AND
				order_number IS NULL
			'''
	cursor.execute(query)
	results = cursor.fetchall()
	prettyResults = {}
	for entry in results:
		discordID = entry[1]
		if not discordID in prettyResults:
			prettyResults[discordID] = []
		prettyResults[discordID].append(entry[0])
		
	conn.close()
	return prettyResults
	

if __name__ == "__main__":
#	result = getMembersFromLastWar()
	result = getMembersWithScoreUnderThreshold(300)
	print(result)
