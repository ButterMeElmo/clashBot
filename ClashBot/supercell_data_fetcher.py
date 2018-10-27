import time
import json
from subprocess import call
import datetime
import pytz

from ClashBot import DateFetcherFormatter

class SupercellDataFetcher:

    date_fetcher_formatter = DateFetcherFormatter()
    
    def getDataFromServer(self):
        call(["node", "myCocAPI.js", ">", "/dev/null"])

    def getFileNames(self, directoryForData, startingFileName, extension, startingTimeStamp):
        date = datetime.datetime.utcfromtimestamp(startingTimeStamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)

        results = []

        endOfToday = self.date_fetcher_formatter.getUTCDateTime().replace(hour = 23, minute=59, second=59)

        while counter_aware_utc_dt <= endOfToday:
            results.append(self.getFileName(directoryForData, startingFileName, extension, counter_aware_utc_dt))
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)
            counter_aware_utc_dt = counter_aware_utc_dt + datetime.timedelta(days=1)
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour = 12)

        return results

    def getFileName(self, directoryForData, startingFileName, extension, date = None):
        directoryForData = str(directoryForData)
        if len(directoryForData) > 0 and directoryForData[-1] != '/' and directoryForData[-1] != '\\':
            directoryForData += "/"
        if date == None:
            date = self.date_fetcher_formatter.getUTCDateTime()
        year = date.year
        month = date.month
        day = date.day
        dateString = '_' + str(year) + '-' + str(month) + '-' + str(day)
        result =  directoryForData + startingFileName + dateString + extension
        return result

    def validateData(self, directoryForData = 'data'):
        """
        Makes sure the data pull was successful.
        """
        datasets = []

        try:
            with open(self.getFileName(directoryForData, "warDetailsLog", ".json"), "r") as file:
                warDetailsSnapshot = json.load(file)
                datasets.append(warDetailsSnapshot)
            with open(self.getFileName(directoryForData, "clanLog", ".json"), "r") as file:
                clanProfileSnapshot = json.load(file)
                datasets.append(clanProfileSnapshot)
            with open(self.getFileName(directoryForData, "warLog", ".json"), "r") as file:
                warLogSnapshot = json.load(file)
                datasets.append(warLogSnapshot)
            with open(self.getFileName(directoryForData, "clanPlayerAchievements", ".json"), "r") as file:
                playerAchievementsSnapshot = json.load(file)
                datasets.append(playerAchievementsSnapshot)
        except FileNotFoundError as e:
            print('A file did not get created: {}'.format(e))
            return False
        except json.decoder.JSONDecodeError as e:
            print('A file does not contain valid json: {}'.format(e))
            return False

        currentTime = self.date_fetcher_formatter.getUTCTimestamp() * 1000

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

