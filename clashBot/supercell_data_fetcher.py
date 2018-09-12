import time
import json
from subprocess import call
import datetime
import pytz

class SupercellDataFetcher:
    def getDataFromServer(self):
        call(["node", "discordBot.js", ">", "/dev/null"])

    def getUTCDateTime(self):
        date = datetime.datetime.utcnow()
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return counter_aware_utc_dt

    def getUTCTimestamp(self):
        return int(self.getUTCDateTime().timestamp())

    def getPrettyTimeStringFromUTCTimestamp(self, timestamp):
        date = datetime.datetime.utcfromtimestamp(timestamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return str(counter_aware_utc_dt)

    def getFileNames(self, startingFileName, extension, startingTimeStamp):
        date = datetime.datetime.utcfromtimestamp(startingTimeStamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)

        results = []

        endOfToday = self.getUTCDateTime().replace(hour = 23, minute=59, second=59)

        while counter_aware_utc_dt <= endOfToday:
            results.append(self.getFileName(startingFileName, extension, counter_aware_utc_dt))
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)
            counter_aware_utc_dt = counter_aware_utc_dt + datetime.timedelta(days=1)
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)

        return results

    def getFileName(self, startingFileName, extension, date = None):
        if date == None:
            date = self.getUTCDateTime()
        year = date.year
        month = date.month
        day = date.day
        dateString = '_' + str(year) + '-' + str(month) + '-' + str(day)
        result =  startingFileName + dateString + extension
        return result

    def validateData(self, directoryForData = 'data'):
        """
        Makes sure the data pull was successful.
        Should I reduce a lot of these exceptions?
        I think yes...
        """
        datasets = []

        try:
            with open(directoryForData + self.getFileName('/warDetailsLog', '.json'), "r") as file:
                warDetailsSnapshot = json.load(file)
                datasets.append(warDetailsSnapshot)
            with open(directoryForData + self.getFileName("/clanLog", ".json"), "r") as file:
                clanProfileSnapshot = json.load(file)
                datasets.append(clanProfileSnapshot)
            with open(directoryForData + self.getFileName("/warLog", ".json"), "r") as file:
                warLogSnapshot = json.load(file)
                datasets.append(warLogSnapshot)
            with open(directoryForData + self.getFileName("/clanPlayerAchievements", ".json"), "r") as file:
                playerAchievementsSnapshot = json.load(file)
                datasets.append(playerAchievementsSnapshot)
        except FileNotFoundError as e:
            print('A file did not get created: {}'.format(e))
            return False
        except json.decoder.JSONDecodeError as e:
            print('A file does not contain valid json: {}'.format(e))
            return False

        currentTime = self.getUTCTimestamp() * 1000

        for dataset in datasets:
            if len(dataset) == 0:
                print('This dataset has no data?')
                return False
            lastSnapshot = dataset[len(dataset) - 1]
            if "timestamp" not in lastSnapshot:
                print('This data had no timetamp.')
                return False
            lastSnapshotTime = lastSnapshot["timestamp"]
            timeDifference = currentTime - lastSnapshotTime
            oneMinute = 60 * 1000
            print("last snapshot was at:  {}".format(lastSnapshotTime))
            print("currently the time is: {}".format(currentTime))
            if timeDifference > oneMinute:
                print('This data is too old.')
                return False
        return True		

def main():
    scdf = SupercellDataFetcher()
    scdf.getDataFromServer()
    valid = scdf.validateData()
    if valid:
        print("Data was retrieved")
    else:
        print("Data was not retrieved")

if __name__ == "__main__":
    main()

