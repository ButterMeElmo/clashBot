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

test_member_1_later = dict(test_member_1)
test_member_1_later['donations'] = 43
test_member_1_later['donationsReceived'] = 161
test_member_1_later['achievements'] = [
        {'name':'Friend in Need','value':1274},
        {'name':'Sharing is caring', 'value':126}
]


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

test_member_2_later = dict(test_member_2)
test_member_2_later['donations'] = 100
test_member_2_later['donationsReceived'] = 101
test_member_2_later['achievements'] = [
        {'name':'Friend in Need','value':97},
        {'name':'Sharing is caring', 'value':3}
]

test_process_player_achievement_files_processes_file_data = [
    {
        'members':[
                dict(test_member_1),
                dict(test_member_2)
        ],
        'timestamp': 1536647109838
    },
    {
        'members':[
                dict(test_member_1_later),
                dict(test_member_2_later)
        ],
        'timestamp': 1536649000001 
    }
]
