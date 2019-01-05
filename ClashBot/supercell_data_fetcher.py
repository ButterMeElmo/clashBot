import datetime
import json
import pytz
import time

from subprocess import call

from ClashBot import DateFetcherFormatter
from ClashBot import ClashOfClansAPI
import os.path


class SupercellDataFetcher:

    def __init__(self):
        with open("configs/supercell.json") as infile:
            config = json.load(infile)
        self.token = config["supercell_token_to_use"]
        self.my_clan_tag = config["my_clan_tag"]
        self.data_directory = config["data_directory"]

    date_fetcher_formatter = DateFetcherFormatter()

    def get_file_names(self, directory_for_data, starting_file_name, extension, starting_time_stamp):
        date = datetime.datetime.utcfromtimestamp(starting_time_stamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)

        results = []

        end_of_today = self.date_fetcher_formatter.get_utc_date_time().replace(hour=23, minute=59, second=59)

        while counter_aware_utc_dt <= end_of_today:
            results.append(self.get_file_name(directory_for_data, starting_file_name, extension, counter_aware_utc_dt))
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour=12)
            counter_aware_utc_dt = counter_aware_utc_dt + datetime.timedelta(days=1)
            counter_aware_utc_dt = counter_aware_utc_dt.replace(hour=12)

        return results

    def get_file_name(self, directory_for_data, starting_file_name, extension, date=None):
        directory_for_data = str(directory_for_data)
        if len(directory_for_data) > 0 and directory_for_data[-1] != '/' and directory_for_data[-1] != '\\':
            directory_for_data += "/"
        if date is None:
            date = self.date_fetcher_formatter.get_utc_date_time()
        year = date.year
        month = date.month
        day = date.day
        date_string = '_' + str(year) + '-' + str(month) + '-' + str(day)
        result = directory_for_data + starting_file_name + date_string + extension
        return result

    def save_data_files(self, file_name, data_to_save, output_dir=None):
        if output_dir is None:
            output_dir = self.data_directory
        if output_dir[-1] != '/':
            output_dir += '/'
        extension = '.json'
        data_file_path = self.get_file_name(output_dir, file_name, extension)
        if os.path.isfile(data_file_path):
            with open(data_file_path, 'r') as in_file:
                current_data = json.load(in_file)
        else:
            current_data = []
        data_to_save['timestamp'] = DateFetcherFormatter().get_utc_timestamp() * 1000
        current_data.append(data_to_save)
        with open(data_file_path, 'w') as outfile:
            output_data = json.dumps(current_data, indent=4)
            outfile.write(output_data)

    def fetch_data(self):
        print('Starting fetching data from clash api')
        coc_client = ClashOfClansAPI(self.token)

        my_clan_tag = self.my_clan_tag[1:]

        clan_profile = coc_client.get_clan_profile(my_clan_tag)

        clan_war_log = coc_client.get_clan_war_log(my_clan_tag)
        current_clan_war = coc_client.get_current_clan_war(my_clan_tag)
        current_war_league_group = coc_client.get_current_war_league_group(my_clan_tag)
        clan_leagues_war_data = {}
        if len(current_war_league_group) > 0:
            rounds = current_war_league_group['rounds']
            for rnd in rounds:
                war_tags = rnd['warTags']
                for war_tag in war_tags:
                    war_tag = war_tag[1:]
                    if "0" == war_tag:
                        continue
                    clan_war_leagues_war = coc_client.get_clan_war_leagues_war(war_tag)
                    clan_leagues_war_data['#'+war_tag] = clan_war_leagues_war

        clan_members = coc_client.get_clan_members(my_clan_tag)
        all_member_achievement_data = {}
        all_member_achievement_data_members = []
        for member in clan_members['items']:
            member_tag = member['tag'][1:]
            member_achievement_data = coc_client.get_player_information(member_tag)
            all_member_achievement_data_members.append(member_achievement_data)
        all_member_achievement_data['members'] = all_member_achievement_data_members

        self.save_data_files('warLog', clan_war_log)
        self.save_data_files('warDetailsLog', current_clan_war)
        self.save_data_files('currentClanWarLeagueGroup', current_war_league_group)
        self.save_data_files('clanWarLeagueWars', clan_leagues_war_data)
        self.save_data_files('clanMembers', clan_members)
        self.save_data_files('clanLog', clan_profile)
        self.save_data_files('clanPlayerAchievements', all_member_achievement_data)

    def get_data_from_server(self):
        self.fetch_data()

    def validate_data(self, directory_for_data=None):
        """
        Makes sure the data pull was successful.
        """
        if directory_for_data is None:
            directory_for_data = self.data_directory

        datasets = []

        try:
            with open(self.get_file_name(directory_for_data, "warDetailsLog", ".json"), "r") as file:
                war_details_snapshot = json.load(file)
                datasets.append(war_details_snapshot)
            with open(self.get_file_name(directory_for_data, "clanLog", ".json"), "r") as file:
                clan_profile_snapshot = json.load(file)
                datasets.append(clan_profile_snapshot)
            with open(self.get_file_name(directory_for_data, "warLog", ".json"), "r") as file:
                war_log_snapshot = json.load(file)
                datasets.append(war_log_snapshot)
            with open(self.get_file_name(directory_for_data, "clanPlayerAchievements", ".json"), "r") as file:
                player_achievements_snapshot = json.load(file)
                datasets.append(player_achievements_snapshot)
        except FileNotFoundError as e:
            print('A file did not get created: {}'.format(e))
            return False
        except json.decoder.JSONDecodeError as e:
            print('A file does not contain valid json: {}'.format(e))
            return False

        current_time = self.date_fetcher_formatter.get_utc_timestamp() * 1000

        for dataset in datasets:
            if len(dataset) == 0:
                print('This dataset has no data?')
                return False
            last_snapshot = dataset[len(dataset) - 1]
            if "timestamp" not in last_snapshot:
                print('This data had no timestamp.')
                return False
            last_snapshot_time = last_snapshot["timestamp"]
            time_difference = current_time - last_snapshot_time
            one_minute = 60 * 1000
            print("last snapshot was at:  {}".format(last_snapshot_time))
            print("currently the time is: {}".format(current_time))
            if time_difference > one_minute:
                print('This data is too old.')
                return False
        return True		


def main():

    try:
        scdf = SupercellDataFetcher()
        scdf.fetch_data()
        valid = scdf.validate_data()
        if valid:
            print("Data was retrieved")
        else:
            print("Data was not retrieved")
    except Exception as e:
        print('Unable to complete fetching data: {}'.format(e))


def init():
    if __name__ == "__main__":
        main()


init()
