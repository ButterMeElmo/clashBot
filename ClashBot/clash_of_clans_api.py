import requests
import json
import config_bot

class ClashOfClansAPI:
    
    def __init__(self, token):
        self.token = token

    def get_clan_war_log(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/warlog'.format(clan_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text

    def get_current_clan_war(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/currentwar'.format(clan_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text
    
    def get_clan_members(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/members'.format(clan_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text

    def get_current_war_league_group(self, clan_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clans/%23{}/currentwar/leaguegroup'.format(clan_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text

    def get_clan_war_leagues_war(self, war_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/clanwarleagues/wars/%23{}'.format(war_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text

    def get_player_information(self, player_tag):
        headers = {'authorization': 'Bearer {}'.format(self.token)}
        url = 'https://api.clashofclans.com/v1/players/%23{}'.format(player_tag)
        response = requests.get(url, headers = headers)    
        print(response.status_code)
        return response.text

def main():
    token = config_bot.supercell_token_to_use
    coc_client = ClashOfClansAPI(token)
    
    my_clan_tag = config_bot.my_clan_tag[1:]

    clan_war_log = coc_client.get_clan_war_log(my_clan_tag)
    current_clan_war = coc_client.get_current_clan_war(my_clan_tag)
    current_war_league_group = coc_client.get_current_war_league_group(my_clan_tag)
    rounds = json.loads(current_war_league_group)['rounds']
    clan_leagues_war_data = {}
    for rnd in rounds:
        war_tags = rnd['warTags']
        for war_tag in war_tags:
            war_tag = war_tag[1:]
            if "0" == war_tag:
                continue
            clan_war_leagues_war = coc_client.get_clan_war_leagues_war(war_tag)
            clan_leagues_war_data['#'+war_tag] = clan_war_leagues_war

    clan_members = coc_client.get_clan_members(my_clan_tag)
    members_loaded = json.loads(clan_members)
    all_member_achievement_data = []
    for member in members_loaded['items']:
        member_tag = member['tag'][1:]
        member_achievement_data = coc_client.get_player_information(member_tag)
        all_member_achievement_data.append(member_achievement_data)

    save_data('file_name', clan_war_log)
    save_data('', current_clan_war)
    save_data('', current_war_league_group)
    save_data('', clan_leagues_war_data)
    save_data('', clan_members)
    save_data('', all_member_achievement_data)

def save_data(file_name, data_to_save):
    output_dir = 'data2/'


if __name__ == "__main__":
    main()
