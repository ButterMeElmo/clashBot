import requests
import json


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
