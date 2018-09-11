import time
import json
from subprocess import call
import datetime
import pytz

def getDataFromServer():
	call(["node", "discordBot.js", ">", "/dev/null"])

def getUTCDateTime():
	date = datetime.datetime.utcnow()
	counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
	return counter_aware_utc_dt

def getUTCTimestamp():
	return int(getUTCDateTime().timestamp())

def getPrettyTimeStringFromUTCTimestamp(timestamp):
	date = datetime.datetime.utcfromtimestamp(1531256703.067)
	counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
	return str(counter_aware_utc_dt)

def getFileNames(startingFileName, extension, startingTimeStamp):

	date = datetime.datetime.utcfromtimestamp(startingTimeStamp)
	counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)

	results = []

	endOfToday = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).replace(hour = 23, minute=59, second=59)

	while counter_aware_utc_dt <= endOfToday:
		results.append(getFileName(startingFileName, extension, counter_aware_utc_dt))
		counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)
		counter_aware_utc_dt = counter_aware_utc_dt + datetime.timedelta(days=1)
		counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)

	return results

def getFileName(startingFileName, extension, date = None):
	if date == None:
		date = datetime.datetime.utcnow()
		date = date.replace(tzinfo=pytz.utc)
	year = date.year
	month = date.month
	day = date.day
	dateString = '_' + str(year) + '-' + str(month) + '-' + str(day)
	result =  startingFileName + dateString + extension
	return result

def validateData():

	datasets = []

	with open(getFileName('data/warDetailsLog', '.json'), "r") as file:
		warDetailsSnapshot = json.load(file)
		datasets.append(warDetailsSnapshot)
	with open(getFileName("data/clanLog", ".json"), "r") as file:
		clanProfileSnapshot = json.load(file)
		datasets.append(clanProfileSnapshot)
	with open(getFileName("data/warLog", ".json"), "r") as file:
		warLogSnapshot = json.load(file)
		datasets.append(warLogSnapshot)
	with open(getFileName("data/clanPlayerAchievements", ".json"), "r") as file:
		playerAchievementsSnapshot = json.load(file)
		datasets.append(playerAchievementsSnapshot)
		
	currentTime = int(round(time.time() * 1000))

	for dataset in datasets:
		lastSnapshot = dataset[len(dataset) - 1]
		lastSnapshotTime = lastSnapshot["timestamp"]
		timeDifference = currentTime - lastSnapshotTime
		oneMinute = 60 * 1000
		print("last snapshot was at:  {}".format(lastSnapshotTime))
		print("currently the time is: {}".format(currentTime))
		if timeDifference > oneMinute:
			return False
	return True		

def main():
	getDataFromServer()
	valid = validateData()
	if valid:
		print("Data was retrieved")
	else:
		print("Data was not retrieved")

if __name__ == "__main__":
	main()

