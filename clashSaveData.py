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
	dataTime = war['timestamp'] / 1000
	
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
		timeToGetSeasonFor = timeToGetSeasonFor / 1000
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
	
	seasonID = getSeasonIDForUTCTimestamp(cursor, clanProfile['timestamp'])

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
	for achievement in allAchievements:
		if achievement['name'] == "Games Champion":
			clan_games_points = achievement['value']

		if achievement['name'] == "Sharing is caring":
			spells_donated = achievement['value']

		if achievement['name'] == "Friend in Need":
			troops_donated_achievement =  achievement['value']

	query = """
		INSERT OR REPLACE INTO
			SCANNED_DATA (member_tag, scanned_data_index, troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, clan_games_points, attacks_won, defenses_won)
		VALUES
			(?, ?, ?, ?, ?, ?, ?, ?, ?);
	"""
	cursor.execute(query, (member_tag, scanned_data_index, troops_donated_monthly, troops_received, spells_donated, troops_donated_achievement, clan_games_points, attacks_won, defenses_won))

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
	scanned_data_index = add_scanned_data_time(cursor, clanPlayerAcievementsEntry['timestamp'])
	for entry in clanPlayerAcievementsEntry['members']:
		addScannedDataToDB(cursor, entry, scanned_data_index)
		addMemberFromAchievements(entry, cursor, clanPlayerAcievementsEntry['timestamp'])

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
		

def populateSeasons(cursor, initialTime):
	startTime = initialTime
	stopTime = datetime.datetime.utcnow()
	aware_utc_dt = stopTime.replace(tzinfo=pytz.utc)
	aware_utc_dt = aware_utc_dt + datetime.timedelta(days=1)
	while startTime < aware_utc_dt.timestamp():
		endTime = getNextSeasonTimeStamp(startTime, False) - 1
#		print('{} - {}'.format(startTime, endTime))
		query = """
			INSERT OR REPLACE INTO
				SEASONS
			VALUES
				(
				COALESCE((SELECT season_ID FROM SEASONS WHERE start_time = ? and end_time = ?), NULL)
				, ?, ?);
		"""
		cursor.execute(query, (startTime, endTime, startTime, endTime))
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
				result = clanGame[2] * 1000 + 1
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
				result = clanGame[1] * 1000 - 1
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

def attemptToFindSiegeMachinesSinceLastProcessed(cursor):
#	query = track
	return

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
	query = '''SELECT MAX(season_ID) FROM SEASONS'''
	cursor.execute(query)
	results = cursor.fetchall()
	if len(results) == 0:
		raise ValueError('no max season id?')		
	max_season_id = results[0][0]
	
	full_run = False
	# do the current season and the previous one
	if previousProcessedTime == 0:
		full_run = True

	# remember, range caps at the upper limit and does NOT run it, so +1 in this case :)
	if full_run:
		iterable = range(1, max_season_id+1)
	else:
		current_season_id = clashAccessData.getSeasonIdForTimestamp(previousProcessedTime)
		iterable = range(current_season_id, max_season_id+1)
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
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, season_start_time * 1000, season_end_time * 1000)
			except clashAccessData.NoDataDuringTimeSpanException:
				# no data from this time period
				continue

			query = '''SELECT troops_donated_monthly, troops_received_monthly, spells_donated_achievement, attacks_won, defenses_won  FROM SCANNED_DATA WHERE member_tag = ? and scanned_data_index >= ? and scanned_data_index <= ?'''
			cursor.execute(query, (member_tag, min_index, max_index))
			results = cursor.fetchall()
			if len(results) == 0:
				# this member wasn't here during this period
				continue
			elif len(results) == 1:
				total_troops_donated, total_troops_received, junk, attacks_won, defenses_won = datapoint
				total_spells_donated = None
			else:
				total_troops_donated = 0
				total_troops_received = 0
				current_iteration_donated = 0
				current_iteration_received = 0
				for datapoint in results:
					if debug:
						print(datapoint)
					# these last two values are used since we only want the last value after the loop
					troops_donated, troops_received, spells_donated, attacks_won, defenses_won = datapoint
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

	for clanGame in clanGames:

		# scanned data has millisecond precision, should probably change that
		clanGameStartTime = clanGame[1] * 1000 
		clanGameEndTime = clanGame[2] * 1000
		clanGameID = clanGame[0]

		if not full_run:
			# if this game ended and has been processed since then, no point redoing it
			if previousProcessedTime > clanGameEndTime / 1000:
				continue

		print('Processing clan games #: ' + str(clanGameID))


		if clanGameStartTime > getDataFromServer.getUTCTimestamp() * 1000:
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
#			print(clanGameStartTime)
			minAllowableTimeForClanGameData = getMinAllowableTimeForClanGameData(clanGames, clanGameID)
			debug = False
			try:
				min_index, max_index = clashAccessData.get_min_and_max_scanned_index_for_min_and_max_scanned_time(cursor, minAllowableTimeForClanGameData, clanGameStartTime)
			except clashAccessData.NoDataDuringTimeSpanException:
				# no data from during this period
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

			debug = False
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
			debug = False
			if debug:
				print('maxAllowableTimeForClanGameData: {}'.format(maxAllowableTimeForClanGameData))
				print('clanGameEndTime: {}'.format(clanGameEndTime))
			if maxAllowableTimeForClanGameData == -2:
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
			debug = False
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

		# october 1 2017, random time
		print('populating all seasons')
		populateSeasons(cursor, 1506884421)

		print('VALIDATE SEASONS PLEASE')
		# go through a known good players data and determine when the season reset, and update that timestamp
		

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
					if war['timestamp'] >= previousProcessedTime*1000:
						processWar(war, cursor)

		clanInfoFileNames = getDataFromServer.getFileNames('data/clanLog', '.json', previousProcessedTime)
		for filename in clanInfoFileNames:
			if os.path.exists(filename):
				print('processing: {}'.format(filename))
				clanInfo = json.load(open(filename))
				for info in clanInfo:
					if info['timestamp'] >= previousProcessedTime*1000:
						processClanProfile(info, cursor)

		achievementsFileNames = getDataFromServer.getFileNames('data/clanPlayerAchievements', '.json', previousProcessedTime)
		for filename in achievementsFileNames:
			if os.path.exists(filename):
				print('processing: {}'.format(filename))
				clanPlayerAcievements = json.load(open(filename))
				for clanPlayerAcievementsEntry in clanPlayerAcievements:
					if clanPlayerAcievementsEntry['timestamp'] >= previousProcessedTime*1000:
						processClanPlayerAcievements(clanPlayerAcievementsEntry, cursor)		

		if previousProcessedTime == 0:
			print('getting linked accounts data')
			useLinkedAccountsStartingPoint(cursor)
			
			print('importing saved gift data')
			importSavedFreeGiftDays(cursor)


		print('processing clan games data from database')
		processClanGamesData(cursor, previousProcessedTime)

		print('processing clan donation/received from database')
		processSeasonData(cursor, previousProcessedTime)

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
