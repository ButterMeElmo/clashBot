import json
import sqlite3
from sqlite3 import Error

resultingData = {}

db_file = "clashData.db"

conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

query = '''
	SELECT discord_tag, is_troop_donator, has_permission_to_set_war_status, time_last_checked_in, trader_shop_reminder_hour FROM DISCORD_ACCOUNTS
	'''
cursor.execute(query)
discordProperties = cursor.fetchall()
discordPropertyList = []
for discordPropertyPiece in discordProperties:
    discordPropertyDict = {}
    discordPropertyDict['discordID'] = discordPropertyPiece[0]
    discordPropertyDict['isDonator'] = discordPropertyPiece[1]
    discordPropertyDict['hasWarPerms'] = discordPropertyPiece[2]
    discordPropertyDict['lastCheckedTime'] = discordPropertyPiece[3]
    discordPropertyDict['traderReminderHour'] = discordPropertyPiece[4]
    discordPropertyList.append(discordPropertyDict)


query = '''
	SELECT discord_tag, member_tag, account_order FROM DISCORD_CLASH_LINKS
	'''
cursor.execute(query)
discordNames = cursor.fetchall()

discordNameList = []
for discordNamePiece in discordNames:
    discordNameDict = {}
    discordNameDict['discordID'] = discordNamePiece[0]
    discordNameDict['member_tag'] = discordNamePiece[1]
    discordNameDict['account_order'] = discordNamePiece[2]
    discordNameList.append(discordNameDict)

resultingData['DISCORD_PROPERTIES'] = discordPropertyList
resultingData['DISCORD_NAMES'] = discordNameList

with open('exported_data/discord_exported_data.json', 'w') as outfile:
    json.dump(resultingData, outfile, indent=4)

# query = '''
# 		SELECT member_tag, free_item_day_of_week, free_item_hour_to_remind, wants_gift_reminder, wants_war_reminder FROM MEMBERS
# 		WHERE
# 			free_item_day_of_week IS NOT NULL
# 		AND
# 			free_item_hour_to_remind IS NOT NULL
# 		AND
# 			wants_gift_reminder IS NOT NULL
# 		OR
# 			wants_war_reminder IS NOT NULL
# 		'''
# cursor.execute(query)
# membersList = []
# members = cursor.fetchall()
# for member in members:
#     memberDict = {}
#     memberDict['member_tag'] = member[0]
#     memberDict['free_item_day_of_week'] = member[1]
#     memberDict['free_item_hour_to_remind'] = member[2]
#     memberDict['wants_gift_reminder'] = member[3]
#     memberDict['wants_war_reminder'] = member[4]
#     membersList.append(memberDict)
#
# with open('manuallyInputtingDataConversion/member_gift_data.json', 'w') as outfile:
#     json.dump(membersList, outfile, indent=4)

conn.close()
