import datetime
import json
import pytz
import time

from subprocess import call

from ClashBot import DateFetcherFormatter
# from ClashBot import ClashOfClansAPI


class SupercellDataFetcher:

    date_fetcher_formatter = DateFetcherFormatter()
    
    def getDataFromServer(self):
        call(["node", "myCocAPI.js", ">", "/dev/null"])
        # ClashOfClansAPI.fetch_and_save()

    def getFileNames(self, directory_for_data, starting_file_name, extension, starting_time_stamp):
        date = datetime.datetime.utcfromtimestamp(starting_time_stamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)

        results = []

        end_of_today = self.date_fetcher_formatter.getUTCDateTime().replace(hour=23, minute=59, second=59)

        while counter_aware_utc_dt <= end_of_today:
            results.append(self.getFileName(directory_for_data, starting_file_name, extension, counter_aware_utc_dt))
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour= 12)
            counter_aware_utc_dt = counter_aware_utc_dt + datetime.timedelta(days=1)
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour= 12)

        return results

    def getFileName(self, directory_for_data, starting_file_name, extension, date = None):
        directory_for_data = str(directory_for_data)
        if len(directory_for_data) > 0 and directory_for_data[-1] != '/' and directory_for_data[-1] != '\\':
            directory_for_data += "/"
        if date is None:
            date = self.date_fetcher_formatter.getUTCDateTime()
        year = date.year
        month = date.month
        day = date.day
        date_string = '_' + str(year) + '-' + str(month) + '-' + str(day)
        result = directory_for_data + starting_file_name + date_string + extension
        return result

    def validateData(self, directoryForData='data'):
        """
        Makes sure the data pull was successful.
        """
        datasets = []

        try:
            with open(self.getFileName(directoryForData, "warDetailsLog", ".json"), "r") as file:
                war_details_snapshot = json.load(file)
                datasets.append(war_details_snapshot)
            with open(self.getFileName(directoryForData, "clanLog", ".json"), "r") as file:
                clan_profile_snapshot = json.load(file)
                datasets.append(clan_profile_snapshot)
            with open(self.getFileName(directoryForData, "warLog", ".json"), "r") as file:
                war_log_snapshot = json.load(file)
                datasets.append(war_log_snapshot)
            with open(self.getFileName(directoryForData, "clanPlayerAchievements", ".json"), "r") as file:
                player_achievements_snapshot = json.load(file)
                datasets.append(player_achievements_snapshot)
        except FileNotFoundError as e:
            print('A file did not get created: {}'.format(e))
            return False
        except json.decoder.JSONDecodeError as e:
            print('A file does not contain valid json: {}'.format(e))
            return False

        current_time = self.date_fetcher_formatter.getUTCTimestamp() * 1000

        for dataset in datasets:
            if len(dataset) == 0:
                print('This dataset has no data?')
                return False
            lastSnapshot = dataset[len(dataset) - 1]
            if "timestamp" not in lastSnapshot:
                print('This data had no timestamp.')
                return False
            last_snapshot_time = lastSnapshot["timestamp"]
            time_difference = current_time - last_snapshot_time
            one_minute = 60 * 1000
            print("last snapshot was at:  {}".format(last_snapshot_time))
            print("currently the time is: {}".format(current_time))
            if time_difference > one_minute:
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


def init():
    if __name__ == "__main__":
        main()


init()
