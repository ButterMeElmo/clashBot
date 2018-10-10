import json

def duplicate_and_add_activity_to_player(player_dict, troops = 52, spells = 7, received = 26):
    """
    input: player dict
    returns: a COPY, modified of the dict

    todo: add attacks and defenses and gold and elixir and DE grab whenever I add that to the saving
    """
    later_player = dict(player_dict)
    
    for achievement in later_player['achievements']:
        if achievement['name'] == 'Friend in Need':
            previous_troops = achievement['value']
        elif achievement['name'] == 'Sharing is caring':
            previous_spells = achievement['value']

    later_player['donations'] += troops + spells
    later_player['donationsReceived'] += received 

    later_player['achievements'] = [
        { 'name' : 'Friend in Need', 'value': previous_troops + troops },
        { 'name' : 'Sharing is caring', 'value': previous_spells + spells }
    ]

test_clan_1 = {
        'tag':'#clan_tag_1',
        'name':'Clan_name_1'
}

test_clan_2 = {
        'tag':'#clan_tag_2',
        'name':'Clan_name_2'
}

test_member_1 = {
    "tag": "#aryb89ba",
    "name": "Richard",
    "townHallLevel": 11,
    "expLevel": 168,
    "trophies": 3605,
    "bestTrophies": 4281,
    "warStars": 544,
    "attackWins": 0,
    "defenseWins": 0,
    "builderHallLevel": 7,
    "versusTrophies": 2975,
    "bestVersusTrophies": 3018,
    "versusBattleWins": 964,
    "role": "admin",
    "donations": 0,
    "donationsReceived": 0,
    "clan": {
        "tag": test_clan_2['tag'],
    },
    "achievements": [
        {'name':'Friend in Need','value':1234},
        {'name':'Sharing is caring', 'value':123}
    ]
}

test_member_2 = {
    "tag": "#8awe6g",
    "name": "Dr. Dre",
    "townHallLevel": 7,
    "expLevel": 12,
    "trophies": 1555,
    "bestTrophies": 1581,
    "warStars": 0,
    "attackWins": 0,
    "defenseWins": 0,
    "builderHallLevel": 7,
    "versusTrophies": 2975,
    "bestVersusTrophies": 3018,
    "versusBattleWins": 964,
    "role": "admin",
    "donations": 28,
    "donationsReceived": 100,
    "clan": {
        "tag": test_clan_2['tag'],
    },
    "achievements": [
        {'name':'Friend in Need','value':25},
        {'name':'Sharing is caring', 'value':3}
    ]
}

test_process_player_achievement_files_processes_file_data = [
    {
        'members':[
                test_member_1,
                test_member_2
        ],
        'timestamp': 1536647109838
    },
    {
        'members':[
                duplicate_and_add_activity_to_player(test_member_1, troops = 13, spells = 2, received = 85),
                duplicate_and_add_activity_to_player(test_member_2, troops = 1, spells = 98, received = 14)
        ],
        'timestamp': 1536649000001
    }
]

test_process_clan_war_details_files_processes_file_data = [
    {},
    {}
]

def get_data_for_test_process_clan_war_details_files_processes_file():
    return test_process_clan_war_details_files_processes_file_data

def get_data_for_test_process_player_achievement_files_processes_file():
    return test_process_player_achievement_files_processes_file_data

def main():
    output = {}
    output['data_for_test_process_player_achievement_files_processes_file'] = test_process_player_achievement_files_processes_file_data
    with open('data_for_test_fetched_data_processor.json', 'w') as outfile:
        json.dump(output, outfile)                          
    

if __name__ == "__main__":
    main()
