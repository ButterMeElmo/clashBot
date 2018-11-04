import requests
import json
import config_bot
from ClashBot import SupercellDataFetcher, DateFetcherFormatter
import os.path


class ClashOfClansAPI:

    # todo better exception handling?? decorator for all exceptions?
    # remove printed messages too

    def __init__(self, token):
        self.token = token

    def get_clan_profile(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}'.format(clan_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('clans/clantag failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_clan_war_log(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/warlog'.format(clan_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('clans/clantag/warlog failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_current_clan_war(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/currentwar'.format(clan_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('clans/clantag/currentwar failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_clan_members(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/members'.format(clan_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('clans/clantag/members failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_current_war_league_group(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/currentwar/leaguegroup'.format(clan_tag)
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return {}
        elif response.status_code != 200:
            raise Exception('clans/clantag/currentwar/leaguegroup failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_clan_war_leagues_war(self, war_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clanwarleagues/wars/%23{}'.format(war_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('clanwarleages/wars/wartag failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)

    def get_player_information(self, player_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/players/%23{}'.format(player_tag)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception('players/membertag failed with status code: {} and body: {}'.format(response.status_code, response.text))
        return json.loads(response.text)


def save_data(file_name, data_to_save):
    output_dir = 'data/'
    scdf = SupercellDataFetcher()
    extension = '.json'
    data_file_path = scdf.getFileName(output_dir, file_name, extension)
    if os.path.isfile(data_file_path):
        with open(data_file_path, 'r') as in_file:
            current_data = json.load(in_file)
    else:
        current_data = []
    data_to_save['timestamp'] = DateFetcherFormatter().getUTCTimestamp()*1000
    current_data.append(data_to_save)
    with open(data_file_path, 'w') as outfile:
        output_data = json.dumps(current_data, indent=4)
        outfile.write(output_data)


def fetch_and_save():
    print('Starting fetching data from clash api')
    token = config_bot.supercell_token_to_use
    coc_client = ClashOfClansAPI(token)

    my_clan_tag = config_bot.my_clan_tag[1:]

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

    save_data('warLog', clan_war_log)
    save_data('warDetailsLog', current_clan_war)
    save_data('currentClanWarLeagueGroup', current_war_league_group)
    save_data('clanWarLeagueWars', clan_leagues_war_data)
    save_data('clanMembers', clan_members)
    save_data('clanLog', clan_profile)
    save_data('clanPlayerAchievements', all_member_achievement_data)


def main():
    try:
        fetch_and_save()
    except Exception as e:
        print('Unable to complete fetching data: {}'.format(e))
    print('Fetching data was completed... one way or the other...')


def init():
    if __name__ == "__main__":
        main()


init()
