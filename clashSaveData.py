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
import os
import clashAccessData
import math

db_file = "clashData.db"
#currentSeasonIDs = {}

newSeasonDetectionThreshold = 15

clanTypes = ['clan', 'opponent']

def convertTime(timeStr):
# 	20180205T055554.000Z
# 	t = '1984-06-02T19:05:00.000Z'
#	print(timeStr)
	parsed_t = dp.parse(timeStr)
	return parsed_t.timestamp()


def addClanToDB(cursor, name, tag):
#	print('implement addClanToDB')
	query = """
		INSERT OR IGNORE INTO
			CLANS
		VALUES
			(?, ?);
	"""
	cursor.execute(query, (tag, name,))

def addMemberToDB(cursor, tag, name, role, townHallLevel, lastSeenInWar):
#	print('implement addMemberToDB')
	currentlyInClan = 1
	if role == None:
		query = """
			INSERT OR REPLACE INTO
				MEMBERS (
						member_tag, 
						member_name, 
						role, 
						trophies, 
						town_hall_level, 
						last_checked_town_hall, 
						in_clan_currently, 
						in_war_currently, 
						free_item_day_of_week, 
						free_item_hour_to_remind, 
						wants_gift_reminder, 
						wants_war_reminder
					)
			VALUES
				(	?, 
					?, 
					(SELECT role FROM MEMBERS WHERE member_tag = ?), 
					(SELECT trophies FROM MEMBERS WHERE member_tag = ?), 
					?, 
					?, 
					?, 
					COALESCE((SELECT in_war_currently FROM MEMBERS WHERE member_tag = ?),0),
					(SELECT free_item_day_of_week FROM MEMBERS WHERE member_tag = ?),
					(SELECT free_item_hour_to_remind FROM MEMBERS WHERE member_tag = ?),
					(SELECT wants_gift_reminder FROM MEMBERS WHERE member_tag = ?),
					(SELECT wants_war_reminder FROM MEMBERS WHERE member_tag = ?)
				);
		"""
		cursor.execute(query, (tag, name, tag, tag, townHallLevel, lastSeenInWar, currentlyInClan, tag, tag,tag,tag,tag,))
	
	elif townHallLevel == None and lastSeenInWar == None:
		query = """
			INSERT OR REPLACE INTO
				MEMBERS (
						member_tag, 
						member_name, 
						role, 
						trophies, 
						town_hall_level, 
						last_checked_town_hall, 
						in_clan_currently, 	
						in_war_currently, 
						free_item_day_of_week, 
						free_item_hour_to_remind, 
						wants_gift_reminder, 
						wants_war_reminder
					)
			VALUES
				(
					?, 
					?, 
					?, 
					(SELECT trophies FROM MEMBERS WHERE member_tag = ?), 
					(SELECT town_hall_level FROM MEMBERS WHERE member_tag = ?), 
					(SELECT last_checked_town_hall FROM MEMBERS WHERE member_tag = ?), 
					?, 
					COALESCE((SELECT in_war_currently FROM MEMBERS WHERE member_tag = ?),0),
					(SELECT free_item_day_of_week FROM MEMBERS WHERE member_tag = ?),
					(SELECT free_item_hour_to_remind FROM MEMBERS WHERE member_tag = ?),
					(SELECT wants_gift_reminder FROM MEMBERS WHERE member_tag = ?),
					(SELECT wants_war_reminder FROM MEMBERS WHERE member_tag = ?)
				);
		"""
		cursor.execute(query, (tag, name, role, tag, tag, tag, 1, tag, tag, tag, tag, tag))
	else:
		print('addMemberToDB what do I do')
		raise ValueError('I don\'t handle all member inputs yet')
	addAccountName(cursor, tag, name)

def addDonationsToDB(cursor, clanTag, memberTag, donated, received, seasonID):
#	print('implement addDonationsToDB')
	query = """
		INSERT OR REPLACE INTO
			TROOP_DONATIONS
		VALUES
			(?, ?, ?, ?, ?);
	"""
	cursor.execute(query, (seasonID, clanTag, memberTag, donated, received))

def addWarAttackToDB(cursor, warAttackDict):

	warID = warAttackDict['warID']
	attackerTag = warAttackDict['attackerTag']
	defenderTag = warAttackDict['defenderTag']
	attackerAttackNumber = warAttackDict['attackerAttackNumber']
	attackerPosition = warAttackDict['attackerPosition']
	defenderPosition = warAttackDict['defenderPosition']
	attackerTownHall = warAttackDict['attackerTownHall']
	defenderTownHall = warAttackDict['defenderTownHall']
	stars = warAttackDict['stars']
	destructionPercentage = warAttackDict['destructionPercentage']
	attackOccurredAfter = warAttackDict['attackOccurredAfter']
	attackOccurredBefore = warAttackDict['attackOccurredBefore']
	orderNumber = warAttackDict['orderNumber']

	# attackOccurredAfter should have a value when the attack has NOT occured (last reading it had not occurred)
	# attackOccurredBefore should have a value when the value has occurred (first reading after it occurred)

	if not attackOccurredAfter == None:
		# attack has not occurred
		query = """
			INSERT OR REPLACE INTO
				WAR_ATTACKS (war_id, attacker_tag, defender_tag, attacker_attack_number, attacker_position, defender_position, attacker_town_hall, defender_town_hall, stars, destruction_percentage, attack_occurred_after, attack_occurred_before, order_number)
			VALUES
				(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
				?
				, ?, ?);
		"""
		cursor.execute(query, (warID, attackerTag, defenderTag, attackerAttackNumber, attackerPosition, defenderPosition, attackerTownHall, 
			defenderTownHall, stars, destructionPercentage, attackOccurredAfter, attackOccurredBefore, orderNumber))
	elif attackOccurredBefore:
		# the attack has now occurred
		query = """
			INSERT OR REPLACE INTO
				WAR_ATTACKS (war_id, attacker_tag, defender_tag, attacker_attack_number, attacker_position, defender_position, attacker_town_hall, defender_town_hall, stars, destruction_percentage, attack_occurred_after, attack_occurred_before, order_number)
			VALUES
				(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
				COALESCE((SELECT attack_occurred_after FROM war_attacks WHERE war_id = ? and attacker_tag = ? and attacker_attack_number = ?), ?),
				COALESCE((SELECT attack_occurred_before FROM war_attacks WHERE war_id = ? and attacker_tag = ? and attacker_attack_number = ?), ?), 
				?);
		"""
		cursor.execute(query, (warID, attackerTag, defenderTag, attackerAttackNumber, attackerPosition, defenderPosition, attackerTownHall, 
			defenderTownHall, stars, destructionPercentage, warID, attackerTag, attackerAttackNumber, attackOccurredAfter, warID, attackerTag, attackerAttackNumber, attackOccurredBefore, orderNumber))
	else:
		raise ValueError('why do neither of these have aligning values?')

def createEmptyWarAttack(warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime):
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
	return warAttackDict		

def addWarToDB(cursor, friendlyTag, opponentTag, status, friendlyStars, opponentStars, friendlyDestructionPercentage, opponentDestructionPercentage, friendlyAttacks, opponentAttacks, warSize, prepStartTime, warStartTime, warEndTime):
	query = """
		INSERT or REPLACE INTO
			WARS (war_id, friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used,
			enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end)
		VALUES
			(COALESCE((SELECT war_id FROM WARS WHERE friendly_tag = ? and enemy_tag = ? and prep_day_start = ?), NULL)
			, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	"""
	cursor.execute(query, (friendlyTag, opponentTag, prepStartTime, friendlyTag, opponentTag, status, friendlyStars, opponentStars, friendlyDestructionPercentage, 
		opponentDestructionPercentage, friendlyAttacks, opponentAttacks, warSize, prepStartTime, warStartTime, warEndTime,))

printedAlready = False
def processWar(war, cursor):

	global printedAlready

	warState = war['state']
#	print(warState)
	if warState == 'notInWar':
		return

	prepStartTime = convertTime(war['preparationStartTime'])
	warStartTime = convertTime(war['startTime'])
	warEndTime = convertTime(war['endTime'])
	warSize = war['teamSize']
	dataTime = int(war['timestamp'] / 1000)
	
	friendlyName = war['clan']['name']
	friendlyTag = war['clan']['tag']
	friendlyStars = war['clan']['stars']
	friendlyDestructionPercentage = war['clan']['destructionPercentage']
	friendlyAttacks = war['clan']['attacks']
	friendlyLevel = war['clan']['clanLevel']

	addClanToDB(cursor, friendlyName, friendlyTag)	

	opponentName = war['opponent']['name']
	opponentTag = war['opponent']['tag']
	opponentStars = war['opponent']['stars']
	opponentDestructionPercentage = war['opponent']['destructionPercentage']
	opponentAttacks = war['opponent']['attacks']
	opponentLevel = war['opponent']['clanLevel']
	
	status = 'in progress'
	
	# war ended
	if dataTime - warEndTime > 0:
		if dataTime - warEndTime < 60:
			#consider throwing away this data and request again in one minute
			pass
		if friendlyStars > opponentStars:
			status = 'won'
		elif friendlyStars < opponentStars:
			status = 'lost'
		elif friendlyDestructionPercentage > opponentDestructionPercentage:
			status = 'won'
		elif friendlyDestructionPercentage < opponentDestructionPercentage:
			status = 'lost'
		else: 
			status = 'tied'
	

	addClanToDB(cursor, opponentName, opponentTag)	

	addWarToDB(cursor, friendlyTag, opponentTag, status, friendlyStars, opponentStars, friendlyDestructionPercentage, opponentDestructionPercentage, friendlyAttacks, opponentAttacks, warSize, prepStartTime, warStartTime, warEndTime)

	cursor.execute(
			'''
			SELECT war_id FROM WARS where friendly_tag = ? and enemy_tag = ? and prep_day_start = ?
			'''
			,(friendlyTag, opponentTag, prepStartTime,))

	warID = cursor.fetchone()[0]

	if not printedAlready:
		print('change this status string')

	if status == 'in progress':
		query = """
			UPDATE MEMBERS
			SET in_war_currently = 0
			"""
		cursor.execute(query)
#		print('setting to 0')
	for clanType in clanTypes:
		for member in war[clanType]['members']:
			memberTag = member['tag']
			memberName = member['name']
			memberTownHall = member['townhallLevel']
			memberMapPosition = member['mapPosition']


			if (clanType == 'clan'):			
				addMemberToDB(cursor, memberTag, memberName, None, memberTownHall, warEndTime)		
				if not printedAlready:
					print('change this status string too...')
					printedAlready = True
				if status == 'in progress':
#					print('setting to 1')
					query = """
						UPDATE MEMBERS
						SET in_war_currently = 1
						WHERE
							member_tag = ?
						"""
					cursor.execute(query, (memberTag,))
					#print('update as in war:')
					#print(memberName)
					#print(memberTag)
					#exit()
			if 'attacks' not in member:
				timeStampAttackLastNotSeen = dataTime
				command = "INSERT OR IGNORE INTO warAttacks () "
				attack1 = createEmptyWarAttack(warID, memberTag, memberMapPosition, memberTownHall, 1, dataTime)
				attack2 = createEmptyWarAttack(warID, memberTag, memberMapPosition, memberTownHall, 2, dataTime)
				addWarAttackToDB(cursor, attack1)
				addWarAttackToDB(cursor, attack2)
			else:

				if len(member['attacks']) == 1:
					timeStampAttackLastNotSeen = dataTime
					command = "INSERT OR IGNORE INTO warAttacks () "
					attack2 = createEmptyWarAttack(warID, memberTag, memberMapPosition, memberTownHall, 2, dataTime)
					addWarAttackToDB(cursor, attack2)			

				for i in range(0,len(member['attacks'])):
					attack = member['attacks'][i]
					
					defenderTag = attack['defenderTag']
					defenderPositionOnWarMap, defenderTownHall = findPositionAndTownHallForMemberTag(war, defenderTag)
				
					warAttackDict = {}
					warAttackDict['warID'] = warID
					warAttackDict['attackerTag'] = memberTag
					warAttackDict['defenderTag'] = defenderTag	
					warAttackDict['attackerAttackNumber'] = i+1
					warAttackDict['attackerPosition'] = memberMapPosition
					warAttackDict['defenderPosition'] = defenderPositionOnWarMap
					warAttackDict['attackerTownHall'] = memberTownHall
					warAttackDict['defenderTownHall'] = defenderTownHall
					warAttackDict['stars'] = attack['stars']
					warAttackDict['destructionPercentage'] = attack['destructionPercentage']
					warAttackDict['attackOccurredAfter'] = None
					warAttackDict['attackOccurredBefore'] = dataTime
					warAttackDict['orderNumber'] = attack['order']
					addWarAttackToDB(cursor, warAttackDict)

				
	if dataTime > warEndTime:
#		remove all unused attacks
		pass
				
def findPositionAndTownHallForMemberTag(war, tag):
	for clanType in clanTypes:
		for member in war[clanType]['members']:
			if member['tag'] == tag:
				memberTownHall = member['townhallLevel']
				memberMapPosition = member['mapPosition']
				return memberMapPosition, memberTownHall

def markMembersNoLongerActive(cursor, profile):
	memberTagsPreviouslyActive = clashAccessData.getAllMembersTagSupposedlyInClan(cursor)
#	print(memberTagsPreviouslyActive)

	memberTagsPreviouslyActiveUpdated = []
	for tag in memberTagsPreviouslyActive:
		memberTagsPreviouslyActiveUpdated.append(tag[0])

	activeTags = []

	for member in profile['memberList']:
		activeTags.append(member['tag'])

	for tag in memberTagsPreviouslyActiveUpdated:
		if tag not in activeTags:	
			#print(member['tag'])

			cursor.execute(
				'''
				UPDATE
					MEMBERS			
				SET
					in_clan_currently = 0
				WHERE
					member_tag = ?
				'''
				,(tag,))

def getSeasonIDForUTCTimestamp(cursor, timeToGetSeasonFor):
	if timeToGetSeasonFor > 2500000000:
		raise ValueError('Timestamp in millisecond')
	#print('getting season id for {}'.format(timeToGetSeasonFor))
	query = """
		SELECT season_ID from SEASONS where start_time < ? and end_time > ?
	"""
	cursor.execute(query,(timeToGetSeasonFor, timeToGetSeasonFor))
	return cursor.fetchone()[0]

def processClanProfile(clanProfile, cursor):
	
	name = clanProfile['name']
	tag = clanProfile['tag']
	
	addClanToDB(cursor, name, tag)
	
	seasonID = getSeasonIDForUTCTimestamp(cursor, int(clanProfile['timestamp']/1000))

#	updateCurrentSeasonInDB(cursor, clanProfile)
	for member in clanProfile['memberList']:
		troopsGiven = member['donations']
		troopsReceived = member['donationsReceived']
		role = member['role']
		name = member['name']
		memberTag = member['tag']

		addMemberToDB(cursor, memberTag, name, role, None, None)		

		addDonationsToDB(cursor, tag, memberTag, troopsGiven, troopsReceived, seasonID)
	
	markMembersNoLongerActive(cursor, clanProfile)

def addAccountName(cursor, playerTag, playerName):
	query = """
		INSERT OR REPLACE INTO
			ACCOUNT_NAMES
		VALUES
			(?, ?);
	"""
	cursor.execute(query, (playerTag, playerName))


def addScannedDataToDB(cursor, data, scanned_data_index):
	member_tag = data['tag']
	troops_donated_monthly = data['donations']
	troops_received = data['donationsReceived']
	allAchievements = data['achievements']
	attacks_won = data['attackWins']
	defenses_won = data['defenseWins']
	town_hall_level = data['townHallLevel']
	for achievement in allAchievements:
		if achievement['name'] == "Games Champion":
			clan_games_points = achievement['value']

		if achievement['name'] == "Sharing is caring":
			spells_donated = achievement['value']

		if achievement['name'] == "Friend in Need":
			troops_donated_achievement =  achievement['value']

	query = """
		INSERT OR REPLACE INTO
			SCANNED_DATA (member_tag, scanned_data_index, troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, clan_games_points, attacks_won, defenses_won, town_hall_level)
		VALUES
			(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
	"""
	cursor.execute(query, (member_tag, scanned_data_index, troops_donated_monthly, troops_received, spells_donated, troops_donated_achievement, clan_games_points, attacks_won, defenses_won, town_hall_level))

	trophies = data['trophies']
	
	query = """
		UPDATE
			MEMBERS
		SET
			trophies = ?
		WHERE
			member_tag = ?
	"""
	cursor.execute(query, (trophies, member_tag))
	
def addMemberFromAchievements(entry, cursor, timestamp):
	query = '''
		INSERT OR REPLACE INTO
			MEMBERS (
					member_tag, 
					member_name, 
					role, 
					trophies, 
					town_hall_level, 
					last_checked_town_hall, 
					in_clan_currently, 
					in_war_currently,
					free_item_day_of_week,
					free_item_hour_to_remind,
					wants_gift_reminder,
					wants_war_reminder
			)
		VALUES
			(
				?, ?, ?, ?, ?, ?, 
				COALESCE((SELECT in_clan_currently FROM MEMBERS WHERE member_tag = ?),0),
				COALESCE((SELECT in_war_currently FROM MEMBERS WHERE member_tag = ?),0),
				(SELECT free_item_day_of_week FROM MEMBERS WHERE member_tag = ?),
				(SELECT free_item_hour_to_remind FROM MEMBERS WHERE member_tag = ?),
				(SELECT wants_gift_reminder FROM MEMBERS WHERE member_tag = ?),
				(SELECT wants_war_reminder FROM MEMBERS WHERE member_tag = ?)
			)
		'''
	tag = entry['tag']
	name = entry['name']
	role = 'no role?, wtf?'
	if 'role' in entry:
		role = entry['role']
	trophies = entry['trophies']
	THLevel = entry['townHallLevel']
	cursor.execute(query, (tag, name, role, trophies, THLevel, timestamp, tag, tag, tag, tag, tag, tag))

def add_scanned_data_time(cursor, timestamp):
	query = '''INSERT OR REPLACE INTO SCANNED_DATA_TIMES (scanned_data_index, time) 
		VALUES (COALESCE((SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time = ?),NULL), ?)'''
	cursor.execute(query, (timestamp, timestamp))
	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time = ?'''
	cursor.execute(query, (timestamp,))
	results = cursor.fetchall()
	if len(results) != 1:
		raise Exception('This time was registered for multiple indexes!')
	else:
		return results[0][0]	

def processClanPlayerAcievements(clanPlayerAcievementsEntry, cursor):
	timestamp = int(clanPlayerAcievementsEntry['timestamp'] / 1000)
	scanned_data_index = add_scanned_data_time(cursor, timestamp)
	for entry in clanPlayerAcievementsEntry['members']:
		addScannedDataToDB(cursor, entry, scanned_data_index)
		addMemberFromAchievements(entry, cursor, timestamp)

def getNextSeasonTimeStamp(timeBeingCalulatedFrom, extraMonth):
	date = datetime.datetime.utcfromtimestamp(timeBeingCalulatedFrom)
	aware_utc_dt = date.replace(tzinfo=pytz.utc)
	if not extraMonth:
		#print('starting with {} which is a monday? ({})'.format(aware_utc_dt.isoformat(), (aware_utc_dt.weekday() == 0)))
		pass
	nextMonth = (aware_utc_dt.month + 1) % 12
	nextYear = aware_utc_dt.year
	if nextMonth == 0:
		nextMonth = 12
	if nextMonth == 1:
		nextYear = aware_utc_dt.year + 1

	if extraMonth == True:
		nextMonth = (nextMonth + 1) % 12
		if nextMonth == 0:
			nextMonth = 12
		if nextMonth == 1:
			nextYear = aware_utc_dt.year + 1
		
	aware_utc_dt = aware_utc_dt.replace(year=nextYear, month=nextMonth, day=1, hour=8, minute=0, second=0, tzinfo=pytz.utc)
	aware_utc_dt = aware_utc_dt - datetime.timedelta(days=aware_utc_dt.weekday())

	result = aware_utc_dt.timestamp()
	if timeBeingCalulatedFrom == result:
		result = getNextSeasonTimeStamp(timeBeingCalulatedFrom, True)
	return result
		

def validateSeasons(cursor, previousProcessedTime):
	full_run = False
	# do the current season and the previous one
	if previousProcessedTime == 0:
		full_run = True

	previously_validated_season_id = clashAccessData.getSeasonIdForTimestamp(previousProcessedTime)
	current_season_id = clashAccessData.getSeasonIdForTimestamp(getDataFromServer.getUTCTimestamp())
	if full_run:
		# our loop will check the border of the previous season as well, so don't want to check the 0th season as it doesn't exist
		iterable = range(2, current_season_id+1)
	else:
		iterable = range(previously_validated_season_id, current_season_id+1)
	for season_id in iterable:
		print('validating a season: {}'.format(season_id))

		query = '''select start_time, end_time from seasons where season_ID = ?'''
		cursor.execute(query, (season_id,))
		results = cursor.fetchall()
		if len(results) != 1:
			raise ValueError('This season does not have proper start and end times')
		season_start_time, season_end_time = results[0]

		start_time_date_time = datetime.datetime.utcfromtimestamp(season_start_time)
		start_time_date_time_aware = start_time_date_time.replace(tzinfo=pytz.utc)
		
		start_of_interval = start_time_date_time_aware - datetime.timedelta(hours = 4)
		start_index = clashAccessData.get_min_index_greater_than_scanned_time(cursor, start_of_interval.timestamp())
		end_of_interval = start_of_interval + datetime.timedelta(hours = 8)
		end_index = clashAccessData.get_min_index_greater_than_scanned_time(cursor, end_of_interval.timestamp())
		
		for current_index in range(start_index, end_index+1):
			newSeasonVote = 0
		
			query = '''SELECT troops_donated_monthly, troops_received_monthly, attacks_won, defenses_won FROM SCANNED_DATA WHERE scanned_data_index = ?'''
			cursor.execute(query, (current_index,))
			results = cursor.fetchall()
			for entry in results:
				donates = entry[0]
				received = entry[1]
				attacks = entry[2]
				defenses = entry[3]
#				if donates < 100 and received < 100 and attacks < 5 and defenses < 5:
				if donates < 100 and received < 100:
					# this is probably a new season
					newSeasonVote += 1

			number_of_members_at_this_time = len(results)

			if (newSeasonVote / number_of_members_at_this_time) > .90:
				# looks like a new season!!

				# see if this is the expected time range
				query = '''SELECT time FROM SCANNED_DATA_TIMES WHERE scanned_data_index = ?'''
				cursor.execute(query, (current_index, ))
				results = cursor.fetchall()
				if len(results) != 1:
					raise ValueError('Some issue occurred here with data times!')

				possible_updated_start_timestamp = results[0][0]				
				
				# this is where the reset should be
				if possible_updated_start_timestamp > season_start_time and possible_updated_start_timestamp < season_end_time:
					print('this season seems to reset at the right time')
					# nothing to do
				else:
					print('this season seems to reset before: {}'.format(possible_updated_start_timestamp))
										
					query = '''SELECT time FROM SCANNED_DATA_TIMES WHERE scanned_data_index = ?'''
					cursor.execute(query, (current_index - 1, ))
					results = cursor.fetchall()
					if len(results) != 1:
						raise ValueError('Some issue occurred here with data times!')
	
					possible_updated_end_timestamp_for_previous_season = results[0][0]				

					# if I want to find when it actually reset, if there is only one top of the hour in between these times, it's almost defintely there...
					midpoint = int((possible_updated_end_timestamp_for_previous_season + possible_updated_start_timestamp)/2)
					new_end = midpoint - 1
					new_start = midpoint

					query = '''UPDATE SEASONS 
						SET start_time = ?
						WHERE season_ID = ?'''

					cursor.execute(query, (new_start, season_id))

					query = '''UPDATE SEASONS 
						SET end_time = ?
						WHERE season_ID = ?'''

					cursor.execute(query, (new_end, season_id-1))
				break

def populateSeasons(cursor, initialTime):
	startTime = initialTime
	stopTime = datetime.datetime.utcnow()
	aware_utc_dt = stopTime.replace(tzinfo=pytz.utc)
	aware_utc_dt = aware_utc_dt + datetime.timedelta(days=1)
	while startTime < aware_utc_dt.timestamp():
		endTime = getNextSeasonTimeStamp(startTime, False) - 1
		query = """INSERT OR REPLACE INTO SEASONS (season_ID, start_time, end_time) SELECT NULL, ?, ? WHERE NOT EXISTS (SELECT season_id FROM SEASONS where end_time > ?)"""
		cursor.execute(query, (startTime, endTime, startTime))
		startTime = endTime + 1

def turnClanGamesStringIntoTimestamp(clangamesString):
	#print("inputting as astring: {}".format(clangamesString))
	clanGamesTimestamp = dateutil.parser.parse(clangamesString)
	clanGamesTimestamp = clanGamesTimestamp.timestamp()
	#print('outputting {}'.format(clanGamesTimestamp))
	return clanGamesTimestamp	

def useOldClanGamesData(cursor):
	clanGames = json.load(open('manuallyInputtingDataConversion/1_clanGamesMain.json'))
	for clanGame in clanGames:
		startTime = turnClanGamesStringIntoTimestamp(clanGame['startTime'])
		stopTime = turnClanGamesStringIntoTimestamp(clanGame['stopTime'])
		personalCap = clanGame['personalCap']
		topTierScore = clanGame['topTierScore']
		minTownHall = 6 #this has been the case for every one so far
		if 'minTownHall' in clanGame:
			minTownHall = clanGame['minTownHall']
			
		query = """
			INSERT OR REPLACE INTO
				CLAN_GAMES (clan_games_ID, start_time, end_time, top_tier_score, personal_limit, min_town_hall)
			VALUES
				(
				COALESCE((SELECT clan_games_ID FROM clan_games WHERE start_time = ? and end_time = ?), NULL)
				, ?, ?, ?, ?, ?);
		"""
		cursor.execute(query, (startTime, stopTime, startTime, stopTime, topTierScore, personalCap, minTownHall))


def useOldClanProfile(cursor):
	clanProfiles = json.load(open('manuallyInputtingDataConversion/3_season1ClanProfile.json'))
	for clanProfile in clanProfiles:
		clanTag = clanProfile['clan_tag']
		timestamp = clanProfile['timestamp']
		seasonID = getSeasonIDForUTCTimestamp(cursor, timestamp)
		members = clanProfile['members']
		for member in members:
			memberTag = member['tag']
			donated = member['donated']
			received = member['received']
			memberName = member['name']
			addMemberToDB(cursor, memberTag, memberName, "unknown", None, None)
			addDonationsToDB(cursor, clanTag, memberTag, donated, received, seasonID)

	clanGamesData = json.load(open('manuallyInputtingDataConversion/2_IndividualScoresClanGames.json'))
	for clanGamesDataSingular in clanGamesData:
		entries = clanGamesDataSingular['entries']
		for entry in entries:
			print(entry)
			memberTag = entry['tag']
			clanGamesID = entry['clanGamesID']
			score = entry['memberScore']
			memberName = entry['name']
			addMemberToDB(cursor, memberTag, memberName, "unknown", None, None)
			query = """
				INSERT OR REPLACE INTO
					CLAN_GAMES_SCORE (member_tag, clan_games_ID, score)
				VALUES
					(?, ?, ?);
			"""
			cursor.execute(query, (memberTag, clanGamesID, score))


def useLinkedAccountsStartingPoint(cursor):
	data = json.load(open('manuallyInputtingDataConversion/discord_exported_data.json'))
	discordProperties = data['DISCORD_PROPERTIES']
	discordNames = data['DISCORD_NAMES']

	for discordProperty in discordProperties:
		query = """
			INSERT OR REPLACE INTO
				DISCORD_PROPERTIES (discord_tag, is_troop_donator, has_permission_to_set_war_status, time_last_checked_in)
			VALUES
				(?, ?, ?, ?);
		"""
		tag = discordProperty['discordID']
		donator = discordProperty['isDonator']
		time = discordProperty['lastCheckedTime']
		war_perms = discordProperty['hasWarPerms']
		print('inserting into properties: {}'.format(tag))
		cursor.execute(query, (tag, donator, war_perms, time))

	for discordName in discordNames:
		query = """
			INSERT OR REPLACE INTO
				DISCORD_NAMES (discord_tag, member_tag, account_order)
			VALUES
				(?, ?, ?);
		"""
		discordTag = discordName['discordID']
		clashTag = discordName['member_tag']
		account_order = discordName['account_order']
		print('inserting into names: {}'.format(discordTag))
		cursor.execute(query, (discordTag, clashTag, account_order))
		
def importSavedFreeGiftDays(cursor):
	data = json.load(open('manuallyInputtingDataConversion/member_gift_data.json'))
	for memberGiftDataEntry in data:
		query = """
			UPDATE MEMBERS
			SET 
				free_item_day_of_week = ?,
				free_item_hour_to_remind = ?,
				wants_war_reminder = ?,
				wants_gift_reminder = ?
			WHERE
				member_tag = ?
		"""
		member_tag = memberGiftDataEntry['member_tag']
		free_item_day_of_week = memberGiftDataEntry['free_item_day_of_week']
		wants_gift_reminder = memberGiftDataEntry['wants_gift_reminder']
		wants_war_reminder = memberGiftDataEntry['wants_war_reminder']
		free_item_hour_to_remind = memberGiftDataEntry['free_item_hour_to_remind']
		cursor.execute(query, (free_item_day_of_week, free_item_hour_to_remind, wants_war_reminder, wants_gift_reminder, member_tag))

def getMinAllowableTimeForClanGameData(clanGameData, currentGamesID):
	result = -1
	if currentGamesID == 0:
		result = 0
	else:
		for clanGame in clanGameData:
			idOfGamesInLoop = clanGame[0]
			if idOfGamesInLoop == currentGamesID - 1:
				result = clanGame[2] + 1
	return result

def getMaxAllowableTimeForClanGameData(clanGameData, currentGamesID):
	"""Returns the last time that is before more points could mess up the data. It currently should return the second before the next clan games start, if the next clan games exist."""
	result = -1
	if currentGamesID == 0:
		result = 0
	else:
		lastClanGame = clanGameData[len(clanGameData)-1]
		if lastClanGame[0] == currentGamesID:
			return -2
		for clanGame in clanGameData:
			if clanGame[0] == currentGamesID + 1:
				result = clanGame[1] - 1
	return result

def DEBUG_ONLY_getMemberNameFromTag(cursor, tag):
	query = '''
		SELECT member_name from members WHERE member_tag = ?
		'''
	cursor.execute(query, (tag,))
	results = cursor.fetchall()
	if len(results) != 1:
		raise ValueError('Theres not exactly one member name for member_tag: {}'.format(tag))
	return results[0][0]

def attemptToFindSiegeMachinesSinceLastProcessed(cursor, previousProcessedTime):
	return
	data = {}

	data[3] = {}
	data[3]['Troops'] = 10
	data[3]['Spells'] = 0
	data[3]['Siege Machine'] = 0

	data[4] = {}
	data[4]['Troops'] = 15
	data[4]['Spells'] = 0
	data[4]['Siege Machine'] = 0

	data[5] = {}
	data[5]['Troops'] = 15
	data[5]['Spells'] = 0
	data[5]['Siege Machine'] = 0

	data[6] = {}
	data[6]['Troops'] = 20
	data[6]['Spells'] = 0
	data[6]['Siege Machine'] = 0

	data[7] = {}
	data[7]['Troops'] = 20
	data[7]['Spells'] = 0
	data[7]['Siege Machine'] = 0

	data[8] = {}
	data[8]['Troops'] = 25
	data[8]['Spells'] = 1
	data[8]['Siege Machine'] = 0

	data[9] = {}
	data[9]['Troops'] = 30
	data[9]['Spells'] = 1
	data[9]['Siege Machine'] = 0

	data[10] = {}
	data[10]['Troops'] = 35
	data[10]['Spells'] = 1
	data[10]['Siege Machine'] = 1

	data[11] = {}
	data[11]['Troops'] = 35
	data[11]['Spells'] = 2
	data[11]['Siege Machine'] = 1

	data[12] = {}
	data[12]['Troops'] = 40
	data[12]['Spells'] = 2
	data[12]['Siege Machine'] = 1
 
	query = '''SELECT MAX(scanned_data_index) FROM SCANNED_DATA_TIMES'''
	cursor.execute(query)
	results = cursor.fetchall()
	if len(results) == 0:
		raise ValueError('no scanned data times?')		
	max_scanned_data_index = results[0][0]
	
	full_run = True # change me
	# do the current season and the previous one
	if previousProcessedTime == 0:
		full_run = True

	# remember, range caps at the upper limit and does NOT run it, so +1 in this case :)
	if full_run:
		iterable = range(1, max_scanned_data_index+1)
	else:
		# change me
		iterable = range(index_that_was_last_done, max_scanned_data_index+1)
	
	last_data_set = {}
	current_data_set = {}

	overall_results = {}

	discarded_previous_data = False
	for scanned_data_index in iterable:

		if discarded_previous_data:
			last_data_set = current_data_set
			discarded_previous_data = False

		debug = False
#		if scanned_data_index == 2546:
#			debug = True
	
		if debug:
			print('processing a scanned_data_index: {}'.format(scanned_data_index))
		query = '''SELECT
			member_tag, troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, town_hall_level
			FROM SCANNED_DATA
			WHERE SCANNED_DATA_INDEX = ?'''
		vars = (scanned_data_index,)
		cursor.execute(query, vars)
		results = cursor.fetchall()

		# let's make this data set more managable
		current_data_set = {}
		for data_point in results:
			member_tag = data_point[0]
			rest_of_data = data_point[1:]
			current_data_set[member_tag] = rest_of_data
		data_modified_as_it_was_pulled = False

		current_list = [*current_data_set.keys()]
		current_list.sort()
		prev_list = [*last_data_set.keys()]
		prev_list.sort()

		# I can examine tracking some data from these periods but it wouldn't be everything, and is a relatively small amount of data
		if current_list != prev_list:
			if debug:
				print('this data should be discarded due to someone leaving or joining')
			discarded_previous_data = True
			continue

		# let's separate out the number of troops+siege sent and given, as well as the number of spells given
		for member_tag in current_data_set:
				# this data needs subtracted
				troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, town_hall_level = current_data_set[member_tag]
				troops_donated_monthly_prev, troops_received_monthly_prev, spells_donated_achievement_prev, troops_donated_achievement_prev, town_hall_level = last_data_set[member_tag]

				# this is simple subtraction using previous achievements/scanned data
				member_donated_troops_and_spells_and_siege = troops_donated_monthly - troops_donated_monthly_prev
				member_received_troops_and_spells_and_siege = troops_received_monthly - troops_received_monthly_prev
				member_donated_spells = spells_donated_achievement - spells_donated_achievement_prev
				member_donated_troops_and_siege = troops_donated_achievement - troops_donated_achievement_prev

				# if these numbers don't match, the data was taken during the middle of a change in data.
				# the next set of data will hopefully line up, so we won't use the current data set
				# in the future, I should consider tracking how long data has been misaligned 
				# as it could be worth dropping the first data set rather than continuing on for a while until someone leaves
				# let's verify our data is good:
				if (member_donated_troops_and_spells_and_siege - member_donated_spells) != member_donated_troops_and_siege:
					data_modified_as_it_was_pulled = True

		if data_modified_as_it_was_pulled:
			# it looks like we pulled data during a change
			if debug:
				print('skipping this index, due to data being modified as it was pulled')
			continue

		# we can know how many were given, but let's see how close we can get, using the same algorithm as we will be forced to use for siege machines
		number_of_spells_known_donated = 0
		number_of_spells_suspected_received = 0 
		number_of_suspected_siege_machines_receieved = 0

		# this can track who appears to have donated the siege and spells, and should replace the two suspected variables above
		appears_to_have_received_siege_machines = {}
		appears_to_have_received_spells = {}

		# first, iterate through and calculate how many spells are known to be given, and therefore received
		for member_tag in current_data_set:
			troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, town_hall_level = current_data_set[member_tag]
			troops_donated_monthly_prev, troops_received_monthly_prev, spells_donated_achievement_prev, troops_donated_achievement_prev, town_hall_level = last_data_set[member_tag]

			# these are the known spells donated
			member_donated_spells = spells_donated_achievement - spells_donated_achievement_prev
			number_of_spells_known_donated += member_donated_spells

			# this is solely debugging
			troops_donated_this_period = troops_donated_monthly - troops_donated_monthly_prev
			if troops_donated_this_period > 0 and debug:
				print('')
				print('TH {} donated total: {}'.format(town_hall_level, troops_donated_this_period))
				print('TH {} donated spells: {}'.format(town_hall_level, (spells_donated_achievement-spells_donated_achievement_prev)))
				print('TH {} donated troops: {}'.format(town_hall_level, (troops_donated_achievement-troops_donated_achievement_prev)))
				print('')

		# next, look at the received and count how many appear to be there
		for member_tag in current_data_set:
			troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, town_hall_level = current_data_set[member_tag]
			troops_donated_monthly_prev, troops_received_monthly_prev, spells_donated_achievement_prev, troops_donated_achievement_prev, town_hall_level = last_data_set[member_tag]

			# this is everything they received combined
			troops_siege_spells_received = troops_received_monthly - troops_received_monthly_prev 

			# determine how many CC refills this looks like by seeing the limits it has
			cc_troop_size = data[town_hall_level]['Troops']
			cc_spell_size = data[town_hall_level]['Spells']
			cc_siege_size = data[town_hall_level]['Siege Machine']
			max_size_per_refill = cc_troop_size + cc_spell_size + cc_siege_size
			num_refills = math.ceil(troops_siege_spells_received / max_size_per_refill)
			# this is the number of troops that appear as leftovers
			remainder = troops_siege_spells_received % cc_troop_size
			#remainder = troops_siege_spells_received - cc_troop_size * num_refills
			
			likely_spells_received = 0
			likely_siege_received = 0

			if troops_siege_spells_received > 0 and debug:
				print('')
				print('TH {} received total: {} on {} refills'.format(town_hall_level, troops_siege_spells_received, num_refills))

			# these are likely_received
			if remainder <= (cc_spell_size + cc_siege_size) * num_refills and remainder > 0:
				list_of_remainders = []
				# if there are a small number of donations, it's hard to differentiate between one archer, one spell, one siege, etc
				# I am assuming these are usually spells for now. Could do something with the known number of spells to increase accuracy
				if num_refills > 1:
					floored_value = int(remainder / num_refills)
					need_to_add = remainder - (floored_value * num_refills)
					for i in range(0, num_refills):
						val_to_use = floored_value
						if need_to_add > 0:
							need_to_add -= 1
							val_to_use += 1
						list_of_remainders.append(val_to_use)
				else:
					list_of_remainders.append(remainder)

				for val in list_of_remainders:
					# here I determine how to distribute remainders
					# 0 happens when there are more refills than the remainder, for example 1, 1, 0 as 3 requests's remainders
					if val == 0:
						continue
					elif val == 1 and cc_spell_size > 0:
						likely_spells_received += 1
					elif val == 2 and cc_spell_size == 2:
						likely_spells_received += 2
					elif val == 2 and cc_spell_size == 1 and cc_siege_size == 1:
						likely_spells_received += 1
						likely_siege_received += 1
					elif val == 3 and cc_spell_size == 2 and cc_siege_size == 1:
						likely_spells_received += 2
						likely_siege_received += 1
					else:
						print('')
						print('troops received: {}'.format(troops_siege_spells_received))
						print('cc size troops: {}'.format(cc_troop_size))
						print('cc size spells: {}'.format(cc_spell_size))
						print('cc size sieges: {}'.format(cc_siege_size))
						print('remainder was: {}'.format(remainder))
						print('num refills: {}'.format(num_refills))	
						print('distributing received as: {}'.format(list_of_remainders))
						print('interpreted as {} spells'.format(likely_spells_received))
						print('interpreted as {} siege'.format(likely_siege_received))
						raise ValueError('inspect these values')
				if debug:
					print('')
					print('troops received: {}'.format(troops_siege_spells_received))
					print('cc size troops: {}'.format(cc_troop_size))
					print('cc size spells: {}'.format(cc_spell_size))
					print('cc size sieges: {}'.format(cc_siege_size))
					print('remainder was: {}'.format(remainder))
					print('num refills: {}'.format(num_refills))	
					print('distributing received as: {}'.format(list_of_remainders))
					print('interpreted as {} spells'.format(likely_spells_received))
					print('interpreted as {} siege'.format(likely_siege_received))

			if likely_siege_received > 0 and cc_siege_size == 0:
				raise ValueError('Examine these values to see why I think there is a siege machine when it cannot be')

			# track who is likely to have received these
			if likely_spells_received > 0:
				number_of_spells_suspected_received += likely_spells_received
				appears_to_have_received_spells[member_tag] = likely_spells_received
			if likely_siege_received > 0:
				number_of_suspected_siege_machines_receieved += likely_siege_received
				appears_to_have_received_siege_machines[member_tag] = likely_siege_received

		# for spells, compare the known given vs likely recevied and determine what to do?



		if number_of_spells_known_donated > 0 or number_of_spells_suspected_received > 0 or number_of_suspected_siege_machines_receieved > 0:	
			if debug == True:
				print('Checking spell data:')
				print('num known spells donated: {}'.format(number_of_spells_known_donated))
				print('num thought spells donated: {}'.format(number_of_spells_suspected_received))
				print('num thought siege donated: {}'.format(number_of_suspected_siege_machines_receieved))
				print('')

		possibly_donated_siege = {}

		for member_tag in current_data_set:
			troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, town_hall_level = current_data_set[member_tag]
			troops_donated_monthly_prev, troops_received_monthly_prev, spells_donated_achievement_prev, troops_donated_achievement_prev, town_hall_level = last_data_set[member_tag]

			troops_donated_during_this_period = troops_donated_monthly - troops_donated_monthly_prev

			# adjust the numbers so that we make sure we don't give credit to a TH 12 for a siege machine if they are the ones who got it
			number_of_siege_machines_suspected_excluding_this_member = number_of_suspected_siege_machines_receieved
			if member_tag in appears_to_have_received_siege_machines:
				number_of_siege_machines_suspected_excluding_this_member -= appears_to_have_received_siege_machines[member_tag]

			# using the adjusted number, check if this member probably donated
			if town_hall_level == 12 and troops_donated_during_this_period > 0 and number_of_siege_machines_suspected_excluding_this_member > 0:
				possibly_donated_siege[member_tag] = number_of_siege_machines_suspected_excluding_this_member

		# these possibly did
		for member_tag in possibly_donated_siege:
			print_possible = False
			if print_possible:
				print('')
				query = '''select member_name from members where member_tag = ?'''
				cursor.execute(query, (member_tag,))
				member_name = cursor.fetchall()[0][0]
				print('there are {} possible sieges up for grabs, and {} had {} donates during this time'.format(number_of_siege_machines_suspected_excluding_this_member, member_name, troops_donated_during_this_period))
				print('')

		# determine if the sum of donates of the possibly_donated_siege list is less or equal to total siege
		# if so, give credit to each member for their total donates
		sum = 0
		for member_tag in possibly_donated_siege:
			sum += possibly_donated_siege[member_tag]
		if sum <= number_of_suspected_siege_machines_receieved:
			# each member gets credit
			for member_tag in possibly_donated_siege:
				print('')
				query = '''select member_name from members where member_tag = ?'''
				cursor.execute(query, (member_tag,))
				member_name = cursor.fetchall()[0][0]
				num_sieges_for_this_member = possibly_donated_siege[member_tag]
				print('{} donated {} sieges'.format(member_name, num_sieges_for_this_member))
				if member_tag not in overall_results:
					overall_results[member_tag] = 0
				overall_results[member_tag] += num_sieges_for_this_member
		elif number_of_suspected_siege_machines_receieved > 0 and len(possibly_donated_siege) == 1:
				print('')
				query = '''select member_name from members where member_tag = ?'''
				cursor.execute(query, (member_tag,))
				member_name = cursor.fetchall()[0][0]
				num_sieges_for_this_member = min(number_of_suspected_siege_machines_receieved, possibly_donated_siege[member_tag])
				print('{} donated {} sieges'.format(member_name, num_sieges_for_this_member))
			
								
		# if the sum of donates of the possibly_donated_siege list is less or equal to total siege, give credit to each member for their total donats
		# if there is only one person, then give them credit for the number of sieges expected, or their donates, whichever is less
		# otherwise, we can't be sure how to break them up

		# we have finished with this data set, and want to use it next time through as the starting point for calculations
		last_data_set = current_data_set


	print('------------')
	for member_tag in overall_results:
		print('')
		query = '''select member_name from members where member_tag = ?'''
		cursor.execute(query, (member_tag,))
		member_name = cursor.fetchall()[0][0]
		num_sieges_for_this_member = overall_results[member_tag]
		print('{} donated {} sieges'.format(member_name, num_sieges_for_this_member))


		# for sieges, compare the likely received vs the possible given
		# for the possible given, can narrow down among the th 12 by looking at nice round numbers of troops given

#		detetermine how many th12 have donated anything during this time.
#		if 0
#			look closer to discover why i am wrong lol
#		if only 1
#			any siege has to be them
#		if more than 1
#			look for them donating 30 vs 31 vs 1
#			30 is probably not a siege machine
#			5 or less is likely
#			31, 36, 41, is very likely
#			
#			update in sql, not in dict like I am
#			member['??']member_donated_siege_i_think += 1
#			member['??']member_donated_troops_i_think -= 1

#def get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, min_timestamp, max_timestamp):
#	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time > ? and time < ?'''
#	cursor.execute(query, (min_timestamp, max_timestamp))
#	results = cursor.fetchall()
#	if len(results) == 0:
#		raise ValueError('unknown values for scanned time')
#	else:
#		min_index = min(results, key = lambda t:t[0])[0]
#		max_index = max(results, key = lambda t:t[0])[0]
#	return min_index, max_index

#def get_min_index_greater_than_scanned_time(cursor, min_timestamp):
#	query = '''SELECT scanned_data_index FROM SCANNED_DATA_TIMES WHERE time > ?'''
#	cursor.execute(query, (min_timestamp))
#	results = cursor.fetchall()
#	if len(results) == 0:
#		raise ValueError('unknown values for scanned time')
#	else:
#		min_index = min(results, key = lambda t:t[0])[0]
#	return min_index

def processSeasonData(cursor, previousProcessedTime):
	full_run = False
	# do the current season and the previous one
	if previousProcessedTime == 0:
		full_run = True

	previously_validated_season_id = clashAccessData.getSeasonIdForTimestamp(previousProcessedTime)
	current_season_id = clashAccessData.getSeasonIdForTimestamp(getDataFromServer.getUTCTimestamp())
	# remember, range caps at the upper limit and does NOT run it, so +1 in this case :)
	if full_run:
		iterable = range(1, current_season_id+1)
	else:
		iterable = range(previously_validated_season_id, current_season_id+1)
	for season_id in iterable:
		print('processing a season: {}'.format(season_id))

		query = '''select start_time, end_time from seasons where season_ID = ?'''
		cursor.execute(query, (season_id,))
		results = cursor.fetchall()
		if len(results) != 1:
			raise ValueError('This season does not have proper start and end times')
		season_start_time, season_end_time = results[0]

		if full_run:
			query = '''select member_tag from members'''
			cursor.execute(query)
			membersInClan = cursor.fetchall()
		else:	
			membersInClan = clashAccessData.getAllMembersTagSupposedlyInClan(cursor)	

		for member_tag in membersInClan:
			member_tag = member_tag[0]
			
			debug = False
			if debug:
				print('processing member: {}'.format(member_tag))

			# get all datapoints for them that fall within the season times
			try:
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, season_start_time, season_end_time)
			except clashAccessData.NoDataDuringTimeSpanException:
				# no data from this time period
				continue

			query = '''SELECT troops_donated_monthly, troops_received_monthly, spells_donated_achievement, attacks_won, defenses_won, scanned_data_index  FROM SCANNED_DATA WHERE member_tag = ? and scanned_data_index >= ? and scanned_data_index <= ?'''
			cursor.execute(query, (member_tag, min_index, max_index))
			results = cursor.fetchall()
			if len(results) == 0:
				# this member wasn't here during this period
				continue
			elif len(results) == 1:
				total_troops_donated, total_troops_received, junk, attacks_won, defenses_won, index = datapoint
				total_spells_donated = None
			else:
				total_troops_donated = 0
				total_troops_received = 0
				current_iteration_donated = 0
				current_iteration_received = 0
				for datapoint in results:
					if debug:
						print(datapoint)
					# the attack and win values are used since we only want the last value after the loop
					troops_donated, troops_received, spells_donated, attacks_won, defenses_won, index = datapoint
					if troops_donated < current_iteration_donated or troops_received < current_iteration_received:
						total_troops_donated += current_iteration_donated
						total_troops_received += current_iteration_received
					current_iteration_donated = troops_donated
					current_iteration_received = troops_received
				total_troops_donated += current_iteration_donated
				total_troops_received += current_iteration_received
	
				total_spells_donated = None			
				initial_spells_donated = results[0][2]
				final_spells_donated = results[len(results)-1][2]
				if initial_spells_donated != None and final_spells_donated != None:
					total_spells_donated = final_spells_donated - initial_spells_donated
				total_troops_donated -= total_spells_donated

			query = '''INSERT OR REPLACE INTO SEASON_HISTORICAL_DATA (season_ID, member_tag, troops_donated, troops_received, spells_donated, attacks_won, defenses_won)	
				SELECT ?, ?, ?, ?, ?, ?, ?
				'''
			second_command_vars = (season_id, member_tag, total_troops_donated, total_troops_received, total_spells_donated, attacks_won, defenses_won)
			cursor.execute(query, second_command_vars)

def processClanGamesData(cursor, previousProcessedTime):
	query = '''
		SELECT * FROM clan_games;
		'''
	cursor.execute(query)
	clanGames = cursor.fetchall()

	full_run = False
	if previousProcessedTime == 0:
		full_run = True

	debug = False

	for clanGame in clanGames:

		# scanned data has millisecond precision, should probably change that
		clanGameStartTime = clanGame[1]
		clanGameEndTime = clanGame[2]
		clanGameID = clanGame[0]

		if not full_run:
			# if this game ended and has been processed since then, no point redoing it
			if previousProcessedTime > clanGameEndTime:
				continue

		print('Processing clan games #: ' + str(clanGameID))

		processingTime = getDataFromServer.getUTCTimestamp()
		if clanGameStartTime > processingTime:
			print('This clan games hasn\'t started yet')
			continue

		if clanGameID <= 15:
			# we didn't have a complete data set, so this must be imported manually
			print('This clan games was too early on, only final results are saved.')
			continue

		membersInClan = clashAccessData.getAllMembersTagSupposedlyInClan(cursor)

		for memberTag in membersInClan:
			#print('')
			memberTag = memberTag[0]
			minAllowableTimeForClanGameData = getMinAllowableTimeForClanGameData(clanGames, clanGameID)
			try:
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, minAllowableTimeForClanGameData, clanGameStartTime)
			except clashAccessData.NoDataDuringTimeSpanException:
				# no data from during this period
				print('There is no data from this period')
				continue

			query = '''SELECT max(scanned_data_index) FROM 
					SCANNED_DATA 
				WHERE
					scanned_data_index >= ? and scanned_data_index <= ? and member_tag = ?
				'''
		#	print(clanGameStartTime)
		#	print(minAllowableTimeForClanGameData)
			cursor.execute(query, (min_index, max_index, memberTag))
			timeBefore = cursor.fetchone()[0]

			if debug:
				print("1")
				print('clanGameStartTime: {}'.format(clanGameStartTime))
				print('clanGameID: {}'.format(clanGameID))
				print('minAllowableTimeForClanGameData: {}'.format(minAllowableTimeForClanGameData))
#			print(timeBefore)
			if timeBefore == None:
				# if we didn't get a time before, then the person didn't join before it started
				# so, let's see if theres a time where they're here but before the games ended
				if debug:
					print("2")

				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, clanGameStartTime, clanGameEndTime)
		
				query = '''SELECT min(scanned_data_index) FROM 
						SCANNED_DATA 
					WHERE
						scanned_data_index >= ? and scanned_data_index <= ? and member_tag = ?
					'''
				if debug:
					print(clanGameStartTime)
					print(clanGameEndTime)
				cursor.execute(query, (min_index, max_index, memberTag))
				timeBefore = cursor.fetchone()[0]
				if timeBefore == None:
					# they weren't here during these games, so move on
					print(DEBUG_ONLY_getMemberNameFromTag(cursor, memberTag) + " seems to not be here during these games")
					continue

#			print(timeBefore)
			query = '''
				SELECT clan_games_points FROM 
					SCANNED_DATA 
				WHERE
					scanned_data_index = ? and member_tag = ?
				'''
			if debug:
				print('timeBefore: {}'.format(timeBefore))
			cursor.execute(query, (timeBefore, memberTag))
			scoreBefore = cursor.fetchone()[0]

			maxAllowableTimeForClanGameData = getMaxAllowableTimeForClanGameData(clanGames, clanGameID)
			if debug:
				print('maxAllowableTimeForClanGameData: {}'.format(maxAllowableTimeForClanGameData))
				print('clanGameEndTime: {}'.format(clanGameEndTime))
			# these are the most recent, potentially ongoing games
			if maxAllowableTimeForClanGameData == -2:
				if clanGameEndTime > processingTime:
					# ongoing games
					query = '''SELECT max(scanned_data_index) FROM
							SCANNED_DATA
						WHERE
							scanned_data_index >= ? and member_tag = ?
						'''
					min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, clanGameStartTime, clanGameEndTime)
					cursor.execute(query, (min_index, memberTag))
				else:
					# most recent games
					min_index = clashAccessData.get_min_index_greater_than_scanned_time(cursor, clanGameEndTime)
					query = '''
						SELECT min(scanned_data_index) FROM 
							SCANNED_DATA 
						WHERE
							scanned_data_index >= ? and member_tag = ?
						'''
					cursor.execute(query, (min_index, memberTag))
			else:
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, clanGameEndTime, maxAllowableTimeForClanGameData)
				query = '''
					SELECT min(scanned_data_index) FROM 
						SCANNED_DATA 
					WHERE
						scanned_data_index >= ? and scanned_data_index <= ? and member_tag = ?
					'''
#				print('----')
#				print(clanGameEndTime)
#				print(maxAllowableTimeForClanGameData)
#				print(memberTag)
				cursor.execute(query, (min_index, max_index, memberTag))
			timeAfter = cursor.fetchone()[0]
			if debug:
				print('ta {}'.format(timeAfter))
			if timeAfter == None:
				
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, clanGameStartTime, clanGameEndTime)
				# if timeAfter is none, they were not here after the last clan games (but before the next ones started)  or the games havent ended
				query = '''
					SELECT max(scanned_data_index) FROM 
						SCANNED_DATA 
					WHERE
						scanned_data_index >= ? and scanned_data_index <= ? and member_tag = ?
					'''
				if debug:
					print(clanGameStartTime)
					print(clanGameEndTime)
					print(memberTag)

				cursor.execute(query, (min_index, max_index, memberTag))
				timeAfter = cursor.fetchone()
				timeAfter = timeAfter[0]
				if timeAfter == None:
					# they also weren't here during the games, so quit
					print(DEBUG_ONLY_getMemberNameFromTag(cursor, memberTag) + " seems to not be here during these games")
					continue
			query = '''
				SELECT clan_games_points FROM 
					SCANNED_DATA 
				WHERE
					scanned_data_index = ? and member_tag = ?
				'''
#			print(memberTag)
			cursor.execute(query, (timeAfter, memberTag))
			scoreAfter = cursor.fetchone()[0]
			
			pointsScored = scoreAfter - scoreBefore
	
			if debug:
				print(scoreAfter)
				print(scoreBefore)

			query = '''
				INSERT OR REPLACE INTO 
					CLAN_GAMES_SCORE (member_tag, clan_games_ID, score)
				VALUES
					(?, ?, ?)
				'''
			if debug:
				print('inserting: cg # {}, {}, {}'.format(clanGameID, memberTag, pointsScored))
				print('')
			cursor.execute(query, (memberTag, clanGameID, pointsScored))
	
def markProcessingTime(cursor, timestamp):
	query = '''
		INSERT OR REPLACE INTO 
			LAST_PROCESSED (count, time)
		VALUES
			(1, ?)
		'''
	cursor.execute(query, (timestamp,))

#def getLastProcessedTime(cursor):
#	query = '''
#		SELECT time
#		FROM
#			LAST_PROCESSED
#		WHERE
#			COUNT = 1
#		'''
#	cursor.execute(query)
#	result = cursor.fetchone()
#	if result == None:
#		result = 0
#	else:
#		result = result[0]
#	return result

def saveData(cursor = None, previousProcessedTime = None):
	""" create a database connection to a SQLite database """
	try:
		cursor_was_none = False
		if cursor == None:
			cursor_was_none = True
			conn = sqlite3.connect(db_file)
#			conn.set_trace_callback(print)
	
			print(sqlite3.version)
			cursor = conn.cursor()
			cursor.execute("PRAGMA foreign_keys = ON")

		if previousProcessedTime == None:
			previousProcessedTime = clashAccessData.getLastProcessedTime()

		date = datetime.datetime.utcnow()
		aware_utc_dt = date.replace(tzinfo=pytz.utc)
		timestampDataProcessed = int(aware_utc_dt.timestamp())

		# starting at october 1 2017, random time
		print('populating all seasons')
		populateSeasons(cursor, 1506884421)

		print('importing clan games start and end times')
		useOldClanGamesData(cursor)

		if previousProcessedTime == 0:
			print('importing manually inputted data')
			useOldClanProfile(cursor)

		warFileNames = getDataFromServer.getFileNames('data/warDetailsLog', '.json', previousProcessedTime)
		for filename in warFileNames:
			print('checking {}'.format(filename))
			if os.path.exists(filename):
				print('processing: {}'.format(filename))
				wars = json.load(open(filename))
				for war in wars:
					if int(war['timestamp'] / 1000) >= previousProcessedTime:
						processWar(war, cursor)

		clanInfoFileNames = getDataFromServer.getFileNames('data/clanLog', '.json', previousProcessedTime)
		for filename in clanInfoFileNames:
			if os.path.exists(filename):
				print('processing: {}'.format(filename))
				clanInfo = json.load(open(filename))
				for info in clanInfo:
					if int(info['timestamp'] / 1000) >= previousProcessedTime:
						processClanProfile(info, cursor)

		achievementsFileNames = getDataFromServer.getFileNames('data/clanPlayerAchievements', '.json', previousProcessedTime)
		for filename in achievementsFileNames:
			if os.path.exists(filename):
				print('processing: {}'.format(filename))
				clanPlayerAcievements = json.load(open(filename))
				for clanPlayerAcievementsEntry in clanPlayerAcievements:
					if int(clanPlayerAcievementsEntry['timestamp'] / 1000) >= previousProcessedTime:
						processClanPlayerAcievements(clanPlayerAcievementsEntry, cursor)		

		if previousProcessedTime == 0:
			print('getting linked accounts data')
			useLinkedAccountsStartingPoint(cursor)
			
			print('importing saved gift data')
			importSavedFreeGiftDays(cursor)


		print('processing clan games data from database')
		processClanGamesData(cursor, previousProcessedTime)

		print('validating season data')
		validateSeasons(cursor, previousProcessedTime)

		print('processing clan donation/received from database')
		processSeasonData(cursor, previousProcessedTime)

		print('searching for siege machines')
		attemptToFindSiegeMachinesSinceLastProcessed(cursor, previousProcessedTime)

		print('marking as completed')
		markProcessingTime(cursor, timestampDataProcessed)
		print('marked')

	finally:
		if cursor_was_none:
			print('committing')
			conn.commit()
			print('closing')
			conn.close()

if __name__ == "__main__":
	saveData()
