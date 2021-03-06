#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import dateutil
import json
import os
import pytz
import time

from ClashBot import DateFetcherFormatter, SupercellDataFetcher
from ClashBot.models import *

from ClashBot import session_scope

printed_already = False

count_to_get_to = 0


class FetchedDataProcessorHelper:

    @staticmethod
    def save_data_helper():
        # this session_scope will commit if an exception is not thrown
        with session_scope() as session:
            fdp = FetchedDataProcessor(session)
            return fdp.save_data()

    @staticmethod
    def last_processed_time_helper():
        with session_scope() as session:
            fdp = FetchedDataProcessor(session)
            return fdp.session.query(LASTPROCESSED.time).filter(LASTPROCESSED.id == 1).scalar()


class FetchedDataProcessor:

    def __init__(self, session):

        self.session = session

        with open("configs/app.json") as infile:
            self.app_config = json.load(infile)
            self.clan_tag_to_scan = self.app_config["my_clan_tag"]
            self.data_directory = self.app_config["data_directory"]

        if not os.path.exists(self.data_directory):
            print('No data to load')
            raise Exception('Data directory does not exist!!')

        # todo should always be false unless we detect there is no time stamp in the db or the db doesn't exist?

        self.previous_processed_time = self.session.query(LASTPROCESSED.time).filter(LASTPROCESSED.id == 1).scalar()
        if self.previous_processed_time is None:
            self.previous_processed_time = 0

        # add trader day base for calculations
        trader_start_calc_time = self.session.query(TRADERDATA.value).filter(TRADERDATA.id == 1).scalar()
        if trader_start_calc_time is None:
            trader_start_calc_time = TRADERDATA()
            trader_start_calc_time.id = 1
            # This should be some date in the past at 12 am GMT
            trader_start_calc_time.value = 1506816000
            self.session.add(trader_start_calc_time)

        if self.previous_processed_time == 0:
            print('Performing initial run!')
            self.initial_run = True
        else:
            self.initial_run = False

        # use these only on initial runs
        # self.members = {} # member tag
        # self.scanned_data = {} # member tag, scanned data time
        # self.war_attacks = {} # member tag, war start time, opponent clan, attack number
        # self.clans = {} # clan tag
        # self.wars = {} # war start time, opponent clan

        # todo where should this live
    def convert_supercell_timestamp_string_to_epoch(self, time_as_string):
        # print("inputting as as string: {}".format(time_as_string))
        # noinspection PyUnresolvedReferences
        timestamp = dateutil.parser.parse(time_as_string).timestamp()
        # print('outputting {}'.format(timestamp))
        return int(timestamp)

    def process_player_achievements(self, clan_player_achievements_entry):
        """
        This method takes in a list of members and their details at a particular timestamp.

        :param clan_player_achievements_entry: a list of all achievements for all players
        """

        # add the scanned data timestamp
        timestamp = int(clan_player_achievements_entry['timestamp'] / 1000)

        # if "scanned_targets" not in clan_player_achievements_entry:
        #     for _, member in self.members.items():
        #         member.clan = None

        all_members_query = self.session.query(MEMBER)
        all_members_query.update({'clan': None})

        # iterate through each player
        for member_entry in clan_player_achievements_entry['members']:

            member_tag = member_entry['tag']

            # for when I managed to pull data as someone left the clan
            if 'clan' in member_entry:
                clan_tag = member_entry['clan']['tag']
                clan_name = member_entry['clan']['name']
                member_role = member_entry['role']
                clan_instance = self.session.query(CLAN).filter(CLAN.clan_tag == clan_tag).one_or_none()
                if clan_instance is None:
                    clan_instance = CLAN()
                    clan_instance.clan_tag = clan_tag
                    clan_instance.clan_name = clan_name
                    self.session.add(clan_instance)
            else:
                clan_tag = None
                clan_name = None
                member_role = None
                print('member is not in a clan')

            king_level = 0
            queen_level = 0
            warden_level = 0
            if 'heroes' in member_entry:
                for hero_entry in member_entry['heroes']:
                    if hero_entry['name'] == 'Barbarian King':
                        king_level = hero_entry['level']
                    elif hero_entry['name'] == 'Archer Queen':
                        queen_level = hero_entry['level']
                    elif hero_entry['name'] == 'Grand Warden':
                        warden_level = hero_entry['level']

            member_instance = self.session.query(MEMBER).filter(MEMBER.member_tag == member_tag).one_or_none()
            if member_instance is None:
                member_instance = MEMBER()
                member_instance.member_tag = member_tag
                self.session.add(member_instance)

            member_instance.member_name = member_entry['name']
            member_instance.role = member_role
            member_instance.trophies = member_entry['trophies']
            member_instance.town_hall_level = member_entry['townHallLevel']
            member_instance.last_updated_time = timestamp
            member_instance.clan_tag = clan_tag
            member_instance.king_level = king_level
            member_instance.queen_level = queen_level
            member_instance.warden_level = warden_level

            # todo - add the names back
            # member_name = member_entry["name"]
            # self.session.query(ACCOUNTNAME).filter()
            # if member_name not in member_added.all_names:
            #     member.all_names.append(ACCOUNTNAME(account_name=member_name))

            troops_donated_achievement = None
            spells_donated_achievement = None
            clan_games_points_achievement = None

            if 'achievements' in member_entry:
                for achievements_entry in member_entry['achievements']:
                    if achievements_entry['name'] == 'Friend in Need':
                        troops_donated_achievement = achievements_entry['value']
                    if achievements_entry['name'] == 'Sharing is caring':
                        spells_donated_achievement = achievements_entry['value']
                    if achievements_entry['name'] == 'Games Champion':
                        clan_games_points_achievement = achievements_entry['value']

            scanned_data_instance = self.session.query(SCANNEDDATA).filter(SCANNEDDATA.member_tag == member_tag).filter(SCANNEDDATA.timestamp == timestamp).one_or_none()
            if scanned_data_instance is None:
                scanned_data_instance = SCANNEDDATA()
                scanned_data_instance.member_tag = member_tag
                scanned_data_instance.troops_donated_monthly = member_entry['donations']
                scanned_data_instance.troops_received_monthly = member_entry['donationsReceived']
                scanned_data_instance.attacks_won = member_entry['attackWins']
                scanned_data_instance.defenses_won = member_entry['defenseWins']
                scanned_data_instance.town_hall_level = member_entry['townHallLevel']
                scanned_data_instance.timestamp = timestamp
                scanned_data_instance.king_level = king_level
                scanned_data_instance.queen_level = queen_level
                scanned_data_instance.warden_level = warden_level
                scanned_data_instance.troops_donated_achievement = troops_donated_achievement
                scanned_data_instance.spells_donated_achievement = spells_donated_achievement
                scanned_data_instance.clan_games_points_achievement = clan_games_points_achievement
                self.session.add(scanned_data_instance)

    def process_player_achievement_files(self):
        count = 0
        scdf = SupercellDataFetcher()
        for player_achievements_file in scdf.get_file_names(self.data_directory, 'clanPlayerAchievements', '.json', self.previous_processed_time):
            if os.path.exists(player_achievements_file):
                print('processing: {}'.format(player_achievements_file))
                start = time.time()

                entries = json.load(open(player_achievements_file))
                for player_achievements_entry in entries:
                    if self.previous_processed_time < int(player_achievements_entry['timestamp'] / 1000):
                        self.process_player_achievements(player_achievements_entry)

                        # self.previous_processed_time_instance.time = int(player_achievements_entry['timestamp']/1000)
                        count += 1
                        if count_to_get_to != 0 and count_to_get_to == count:
                            return
                end = time.time()
                print(end - start)

    def process_clan_war_league_entries(self, entries, clan_tag_to_scan=None):
        if clan_tag_to_scan is None:
            clan_tag_to_scan = self.clan_tag_to_scan
        # todo fix the data...
        for key, value in entries.items():
            if key != "timestamp":
                war = value
                clan_tag = war["clan"]["tag"]
                opponent_tag = war["opponent"]["tag"]
                if clan_tag == clan_tag_to_scan:
                    pass
                elif opponent_tag == clan_tag_to_scan:
                    # flip these as we assume we are always the friendly clan
                    clan = war.pop("opponent")
                    opponent = war.pop("clan")
                    war["clan"] = clan
                    war["opponent"] = opponent
                else:
                    # we aren't in this war, so we don't really care about it, yet
                    continue

                # remove all our members, we only want to process the ones actually in war
                clan_members = war["clan"].pop("members")
                war["clan"]["members"] = []

                # get opponenents members, but don't clear them. They're used to process ours, but not saved anyways.
                opponent_members = war["opponent"]["members"]

                # see if we have 15 attacks to determine who we had in war
                clan_members_in_cwl = {}
                for member in clan_members:
                    if "attacks" in member:
                        member_tag = member["tag"]
                        clan_members_in_cwl[member_tag] = member

                # if we couldn't tell who all 15 were, iterate through opponents and try to find the rest
                if len(clan_members_in_cwl) != 15:

                    # save all the clan members
                    clan_members_to_scan = {}
                    for member in clan_members:
                        member_tag = member["tag"]
                        clan_members_to_scan[member_tag] = member

                    # iterate through the opponents
                    for member in opponent_members:
                        # if the opponent used his attack, see if we have added that person yet
                        if "attacks" in member:
                            clan_member_tag = member["attacks"][0]["defenderTag"]
                            if clan_member_tag not in clan_members_in_cwl:
                                clan_members_in_cwl[clan_member_tag] = clan_members_to_scan[clan_member_tag]

                for member in clan_members_in_cwl.values():
                    war["clan"]["members"].append(member)

                war["timestamp"] = entries["timestamp"]
                # now, determine what members are in the war
                self.process_clan_war_details(war, is_clan_war_league=True)

    def process_clan_war_league_files(self):
        count = 0
        scdf = SupercellDataFetcher()
        for clan_war_league_wars_file in scdf.get_file_names(self.data_directory, 'clanWarLeagueWars', '.json', self.previous_processed_time):
            if os.path.exists(clan_war_league_wars_file):
                print('processing: {}'.format(clan_war_league_wars_file))
                start = time.time()

                entries = json.load(open(clan_war_league_wars_file))
                for clan_war_league_entries in entries:
                    if self.previous_processed_time < int(clan_war_league_entries['timestamp'] / 1000):
                        self.process_clan_war_league_entries(clan_war_league_entries)

                        # self.previous_processed_time_instance.time = int(player_achievements_entry['timestamp']/1000)
                        count += 1
                        if count_to_get_to != 0 and count_to_get_to == count:
                            return
                end = time.time()
                print(end - start)

    def process_clan_war_details(self, war, is_clan_war_league=False):

        global printed_already

        # if there is no active war being passed, quit
        war_state = war['state']
        # print(war_state)
        if war_state == 'notInWar':
            return

        # get basic war data
        prep_start_time = self.convert_supercell_timestamp_string_to_epoch(war['preparationStartTime'])
        war_start_time = self.convert_supercell_timestamp_string_to_epoch(war['startTime'])
        war_end_time = self.convert_supercell_timestamp_string_to_epoch(war['endTime'])
        war_size = war['teamSize']
        data_time = int(war['timestamp'] / 1000)

        friendly_name = war['clan']['name']
        friendly_tag = war['clan']['tag']
        friendly_stars = war['clan']['stars']
        friendly_destruction_percentage = war['clan']['destructionPercentage']
        friendly_attacks = war['clan']['attacks']
        friendly_level = war['clan']['clanLevel']

        # make sure our clan is in the DB
        friendly_clan_instance = self.session.query(CLAN).filter(CLAN.clan_tag == friendly_tag).one_or_none()
        if friendly_clan_instance is None:
            friendly_clan_instance = CLAN()
            friendly_clan_instance.clan_tag = friendly_tag
            friendly_clan_instance.clan_name = friendly_name
            self.session.add(friendly_clan_instance)

        opponent_name = war['opponent']['name']
        opponent_tag = war['opponent']['tag']
        opponent_stars = war['opponent']['stars']
        opponent_destruction_percentage = war['opponent']['destructionPercentage']
        opponent_attacks = war['opponent']['attacks']
        opponent_level = war['opponent']['clanLevel']

        status = 'in progress'

        # war ended
        if data_time - war_end_time > 0:
            if data_time - war_end_time < 60:
                # consider throwing away this data and request again in one minute
                pass
            if friendly_stars > opponent_stars:
                status = 'won'
            elif friendly_stars < opponent_stars:
                status = 'lost'
            elif friendly_destruction_percentage > opponent_destruction_percentage:
                status = 'won'
            elif friendly_destruction_percentage < opponent_destruction_percentage:
                status = 'lost'
            else:
                status = 'tied'

        # make sure the opponent clan exists in our DB
        opponent_clan_instance = self.session.query(CLAN).filter(CLAN.clan_tag == opponent_tag).one_or_none()
        if opponent_clan_instance is None:
            opponent_clan_instance = CLAN()
            opponent_clan_instance.clan_tag = opponent_tag
            opponent_clan_instance.clan_name = opponent_name
            self.session.add(opponent_clan_instance)

        # make sure the war exists, create it if not
        war_instance = self.session.query(WAR).filter(WAR.prep_day_start == prep_start_time) \
            .filter(WAR.enemy_clan == opponent_clan_instance) \
            .filter(WAR.friendly_clan == friendly_clan_instance).one_or_none()

        if war_instance is None:
            war_instance = WAR()
            war_instance.enemy_clan = opponent_clan_instance
            war_instance.friendly_clan = friendly_clan_instance
            war_instance.prep_day_start = prep_start_time
            war_instance.is_clan_war_league_war = is_clan_war_league
            war_instance.war_size = war_size
            self.session.add(war_instance)

        # if this is false, then this is a CWL war from the non CWL files, so it has been handled already, skip it.
        if war_instance.is_clan_war_league_war != is_clan_war_league:
            # cwl called from standard war files will be messed up and has already been processed
            return

        # update war variables that can change (time change change due to maintenance breaks)
        war_instance.result = status
        war_instance.friendly_stars = friendly_stars
        war_instance.enemy_stars = opponent_stars
        war_instance.friendly_percentage = friendly_destruction_percentage
        war_instance.enemy_percentage = opponent_destruction_percentage
        war_instance.friendly_attacks_used = friendly_attacks
        war_instance.enemy_attacks_used = opponent_attacks
        war_instance.war_day_start = war_start_time
        war_instance.war_day_end = war_end_time

        # todo
        if not printed_already and False:
            print('change this status string')

        possible_clan_types = ['clan', 'opponent']

        # earlier we were saving the opponents attacks too. do we want to add that back?
        # # iterate through each clan
        # for clan_type in possible_clan_types:

        # iterate through our attacks
        clan_type = "clan"
        clan_tag = war['clan']['tag']
        for member in war[clan_type]['members']:

            attack1 = None
            attack2 = None

            member_tag = member['tag']
            member_name = member['name']
            member_town_hall = member['townhallLevel']
            member_map_position = member['mapPosition']

            # this could be removed for the moment, but if we decide to process the enemy, I will need it back.
            if clan_type == 'clan':

                # ensure the member exists
                member_instance = self.session.query(MEMBER).filter(MEMBER.member_tag == member_tag).one_or_none()
                if member_instance is None:
                    member_instance = MEMBER()
                    member_instance.member_tag = member_tag
                    self.session.add(member_instance)

                if not printed_already:
                    print('change this status string too...')
                    printed_already = True

                # add the war participation if it exists
                if war_instance.clan_war_identifier in member_instance.war_participations:
                    war_participation_instance = member_instance.war_participations[war_instance.clan_war_identifier]
                else:
                    # otherwise create it
                    war_participation_instance = WARPARTICIPATION()
                    war_participation_instance.war = war_instance
                    war_participation_instance.member = member_instance
                    war_participation_instance.is_clan_war_league_war = war_instance.is_clan_war_league_war
                    self.session.add(war_participation_instance)
                    # self.session.flush()

                if war_participation_instance.is_clan_war_league_war == 2 and is_clan_war_league is True:
                    # if we get here, this was manually entered so this attack should already be created.
                    # This would be one that was manually entered and is now showing up on scans of data too.
                    war_participation_instance.is_clan_war_league_war = 1
                    war_participation_instance.attack1.attacker_position = member_map_position
                    war_participation_instance.attack1.attacker_town_hall = member_town_hall

                # always make sure we have a war attack 1 for this member in this war
                if war_participation_instance.attack1 is None:
                    attack_1_instance = WARATTACK()
                    attack_1_instance.attacker_attack_number = 1
                    attack_1_instance.war = war_instance
                    attack_1_instance.member = member_instance
                    attack_1_instance.attacker_tag = member_tag
                    attack_1_instance.attacker_position = member_map_position
                    attack_1_instance.attacker_town_hall = member_town_hall
                    war_participation_instance.attack1 = attack_1_instance
                else:
                    attack_1_instance = war_participation_instance.attack1

                # if not a CWL, make sure we have a war attack 1 for this member in this war
                if not war_instance.is_clan_war_league_war:
                    if war_participation_instance.attack2 is None:
                        attack_2_instance = WARATTACK()
                        attack_2_instance.attacker_attack_number = 2
                        attack_2_instance.war = war_instance
                        attack_2_instance.member = member_instance
                        attack_2_instance.attacker_tag = member_tag
                        attack_2_instance.attacker_position = member_map_position
                        attack_2_instance.attacker_town_hall = member_town_hall
                        war_participation_instance.attack2 = attack_2_instance
                    else:
                        attack_2_instance = war_participation_instance.attack2

                if 'attacks' not in member:

                    # update these times if the attacks haven't occurred
                    attack_1_instance.attack_occurred_after = data_time
                    if not war_instance.is_clan_war_league_war:
                        attack_2_instance.attack_occurred_after = data_time
                else:
                    # if only one attack has occurred, update the second one's last time not seen
                    if len(member['attacks']) == 1 and not war_instance.is_clan_war_league_war:
                        attack_2_instance.attack_occurred_after = data_time

                    # add the attacks that have occurred
                    for i in range(0, len(member['attacks'])):
                        attack = member['attacks'][i]

                        defender_tag = attack['defenderTag']

                        def find_position_and_town_hall_for_member_tag(parsing_war, parsing_tag):
                            for parsing_clan_type in possible_clan_types:
                                for parsing_member in parsing_war[parsing_clan_type]['members']:
                                    if parsing_member['tag'] == parsing_tag:
                                        parsing_member_town_hall = parsing_member['townhallLevel']
                                        parsing_member_map_position = member['mapPosition']
                                        return parsing_member_map_position, parsing_member_town_hall

                        defender_position_on_war_map, defender_town_hall = find_position_and_town_hall_for_member_tag(war, defender_tag)

                        if i == 0:
                            attack_1_instance.defender_tag = defender_tag
                            attack_1_instance.defender_position = defender_position_on_war_map
                            attack_1_instance.defender_town_hall = defender_town_hall
                            attack_1_instance.stars = attack['stars']
                            attack_1_instance.destruction_percentage = attack['destructionPercentage']
                            attack_1_instance.attack_occurred_before = data_time
                            attack_1_instance.order_number = attack['order']
                        else:
                            attack_2_instance.defender_tag = defender_tag
                            attack_2_instance.defender_position = defender_position_on_war_map
                            attack_2_instance.defender_town_hall = defender_town_hall
                            attack_2_instance.stars = attack['stars']
                            attack_2_instance.destruction_percentage = attack['destructionPercentage']
                            attack_2_instance.attack_occurred_before = data_time
                            attack_2_instance.order_number = attack['order']

    def process_clan_war_details_files(self):
        count = 0
        scdf = SupercellDataFetcher()
        for clan_war_details_file in scdf.get_file_names(self.data_directory, 'warDetailsLog', '.json', self.previous_processed_time):
            if os.path.exists(clan_war_details_file):
                print('processing: {}'.format(clan_war_details_file))
                entries = json.load(open(clan_war_details_file))
                for clan_war_details_entry in entries:
                    if self.previous_processed_time < int(clan_war_details_entry['timestamp'] / 1000):
                        self.process_clan_war_details(clan_war_details_entry)

                        count += 1
                        if count_to_get_to != 0 and count_to_get_to == count:
                            return

    def import_linked_accounts_to_db(self):

        filename = 'exported_data/discord_exported_data.json'
        if not os.path.exists(filename):
            print('No discord data to load')
            return

        data = json.load(open(filename))
        discord_properties = data['DISCORD_PROPERTIES']
        discord_names = data['DISCORD_NAMES']

        discord_account_instances = {}

        # self.session.flush()

        for discord_account in discord_properties:
            discord_account_instance = DISCORDACCOUNT()
            self.session.add(discord_account_instance)
            discord_tag = discord_account['discord_id']
            discord_account_instance.discord_tag = discord_tag
            discord_account_instance.is_troop_donator = discord_account['is_donator']
            discord_account_instance.has_permission_to_set_war_status = discord_account['has_war_permissions']
            discord_account_instance.time_last_checked_in = discord_account['time_last_checked_in']
            discord_account_instance.trader_shop_reminder_hour = discord_account['trader_reminder_hour']
            discord_account_instances[discord_tag] = discord_account_instance

        # self.session.flush()

        members = self.session.query(MEMBER).all()

        for discord_name in discord_names:

            discord_clash_link_instance = DISCORDCLASHLINK()
            discord_clash_link_instance.account_order = discord_name['account_order']
            clash_tag_looking_for = discord_name['member_tag']
            found = False
            for member in members:
                if member.member_tag == clash_tag_looking_for:
                    discord_clash_link_instance.clash_account = member
                    found = True

            if not found:
                print("Creating dummy member")
                dummy = MEMBER()
                dummy.member_tag = clash_tag_looking_for
                discord_clash_link_instance.clash_account = dummy

            discord_tag = discord_name['discord_id']
            discord_clash_link_instance.discord_account = discord_account_instances[discord_tag]
            self.session.add(discord_clash_link_instance)

    def import_member_data_to_db(self):

        filename = 'exported_data/member_data.json'
        if not os.path.exists(filename):
            print('No member data to load')
            return

        member_data = json.load(open(filename))
        for member_data_instance in member_data:
            member_tag = member_data_instance["member_tag"]
            trader_rotation_offset = member_data_instance["trader_rotation_offset"]

            member_instance = self.session.query(MEMBER).filter(MEMBER.member_tag == member_tag).all()
            if member_instance is None:
                member_instance = MEMBER()
                member_instance.member_tag = member_tag
                self.session.add(member_instance)

            member_instance.trader_rotation_offset = trader_rotation_offset

    def import_trader_data_to_db(self):

        # read in the trader data json
        trader_data = json.load(open('clash_common_data/trader_cycle.json'))

        # see if the data needs updated - either it didn't exist or is older than what we have
        updating = False
        trader_data_updated = trader_data["last_updated"]
        trader_data_updated_instance = self.session.query(TRADERDATA).filter(TRADERDATA.id == 3).one_or_none()
        if trader_data_updated_instance is None:
            # didn't exist
            trader_data_updated_instance = TRADERDATA()
            trader_data_updated_instance.id = 3
            trader_data_updated_instance.value = trader_data_updated
            updating = True
            self.session.add(trader_data_updated_instance)
        else:
            # existed, lets see if it's older than the data we just read in
            if trader_data_updated_instance.value < trader_data_updated:
                updating = True
                trader_data_updated_instance.value = trader_data_updated

        # this is if either of the two above cases are true
        if updating:

            print("Updating trader data")

            # get/create the instance where cycle length is stored
            trader_cycle_length_instance = self.session.query(TRADERDATA).filter(TRADERDATA.id == 2).one_or_none()
            if trader_cycle_length_instance is None:
                trader_cycle_length_instance = TRADERDATA()
                trader_cycle_length_instance.id = 2
                self.session.add(trader_cycle_length_instance)

            # add/update the trader cycle length
            cycle_length = trader_data["cycle_length"]
            trader_cycle_length_instance.value = cycle_length

            # delete all the old entryies
            self.session.query(TRADERITEM).delete()

            # read in the new ones
            for day_number, list_of_items in trader_data["high_value_days"].items():
                day_number = int(day_number)
                for item in list_of_items:
                    item_instance = TRADERITEM()
                    item_instance.cost = item["cost"]
                    item_instance.day_in_rotation = day_number
                    item_instance.name = item["type"]
                    self.session.add(item_instance)

    def import_clan_games_metadata(self):

        clan_games_metadata = json.load(open('clash_common_data/clan_games_metadata.json'))

        clan_games = self.session.query(CLANGAME).all()
        clan_game_start_times = set()
        for clan_game_instance in clan_games:
            clan_game_start_times.add(clan_game_instance.start_time)

        for clan_game in clan_games_metadata:

            start_time = self.convert_supercell_timestamp_string_to_epoch(clan_game['startTime'])
            stop_time = self.convert_supercell_timestamp_string_to_epoch(clan_game['stopTime'])
            personal_cap = clan_game['personalCap']
            top_tier_score = clan_game['topTierScore']
            min_town_hall = 6

            if start_time not in clan_game_start_times:
                clan_game_to_add = CLANGAME()
                clan_game_to_add.start_time = start_time
                clan_game_to_add.end_time = stop_time
                clan_game_to_add.top_tier_score = top_tier_score
                clan_game_to_add.personal_limit = personal_cap
                clan_game_to_add.min_town_hall = min_town_hall
                self.session.add(clan_game_to_add)

    def get_next_season_time_stamp(self, time_being_calculated_from, extra_month=False):
        date = datetime.datetime.utcfromtimestamp(time_being_calculated_from)
        aware_utc_dt = date.replace(tzinfo=pytz.utc)
        if not extra_month:
            # print('starting with {} which is a monday? ({})'.format(aware_utc_dt.isoformat(), (aware_utc_dt.weekday() == 0)))
            pass
        next_month = (aware_utc_dt.month + 1) % 12
        next_year = aware_utc_dt.year
        if next_month == 0:
            next_month = 12
        if next_month == 1:
            next_year = aware_utc_dt.year + 1

        if extra_month:
            next_month = (next_month + 1) % 12
            if next_month == 0:
                next_month = 12
            if next_month == 1:
                next_year = aware_utc_dt.year + 1

        aware_utc_dt = aware_utc_dt.replace(year=next_year, month=next_month, day=1, hour=8, minute=0, second=0,
                                            tzinfo=pytz.utc)
        aware_utc_dt = aware_utc_dt - datetime.timedelta(days=aware_utc_dt.weekday())

        result = aware_utc_dt.timestamp()
        if time_being_calculated_from == result:
            result = self.get_next_season_time_stamp(time_being_calculated_from, True)
        return result

    # october 1 2017, random time
    def populate_seasons_in_db(self, initial_time=1506884421):
        if self.initial_run:
            start_time = initial_time
        else:
            last_created_season = self.session.query(SEASON).order_by(SEASON.end_time.desc()).first()
            start_time = last_created_season.end_time + 1
        stop_time = datetime.datetime.utcnow()
        aware_utc_dt = stop_time.replace(tzinfo=pytz.utc)
        aware_utc_dt = aware_utc_dt + datetime.timedelta(days=1)

        all_seasons_start_times = set()
        all_seasons_instances = self.session.query(SEASON).all()
        for season_instance in all_seasons_instances:
            all_seasons_start_times.add(int(season_instance.start_time))

        while start_time < aware_utc_dt.timestamp():
            end_time = self.get_next_season_time_stamp(start_time) - 1

            if int(start_time) not in all_seasons_start_times:
                print("adding")
                instance = SEASON()
                instance.start_time = int(start_time)
                instance.end_time = int(end_time)
                self.session.add(instance)

            start_time = end_time + 1

    def validate_seasons_in_db(self):

        season_query = self.session.query(SEASON)

        full_run = False
        if self.initial_run:
            full_run = True
            print('performing full run')

        if full_run:
            print('full run')
            season_query = season_query.filter(SEASON.season_id > 1)
        else:
            current_season_instance = self.session.query(SEASON) \
                .filter(SEASON.start_time <= self.previous_processed_time) \
                .filter(SEASON.end_time >= self.previous_processed_time).one_or_none()

            last_season_instance = self.session.query(SEASON).filter(SEASON.end_time == current_season_instance.start_time-1).one()

            if last_season_instance is None:
                raise Exception("Why are you asking for this time? No season matches it.")

            season_query = season_query.filter(SEASON.end_time >= last_season_instance.end_time)

        season_instances = season_query.all()

        prev_instance = season_instances[0]
        for season_instance in season_instances[1:]:
            print('validating a season: {}'.format(season_instance.season_id))

            season_start_time = season_instance.start_time
            season_end_time = season_instance.end_time

            start_time_date_time = datetime.datetime.utcfromtimestamp(season_start_time)
            start_time_date_time_aware = start_time_date_time.replace(tzinfo=pytz.utc)

            start_of_interval_calc = start_time_date_time_aware - datetime.timedelta(hours=24)
            start_of_interval = start_of_interval_calc.timestamp()
            end_of_interval = (start_of_interval_calc + datetime.timedelta(hours=48)).timestamp()

            all_scanned_data_relevant_to_season = self.session.query(SCANNEDDATA).filter(SCANNEDDATA.timestamp >= start_of_interval) \
                .filter(SCANNEDDATA.timestamp <= end_of_interval).all()

            data_around_season_as_dict = {}
            for scanned_data_instance in all_scanned_data_relevant_to_season:
                if scanned_data_instance.timestamp not in data_around_season_as_dict:
                    data_around_season_as_dict[scanned_data_instance.timestamp] = []
                data_around_season_as_dict[scanned_data_instance.timestamp].append(scanned_data_instance)

            previous_timestamp = 0
            for timestamp in data_around_season_as_dict:
                new_season_vote = 0

                scanned_data_instances_at_particular_time = data_around_season_as_dict[timestamp]

                for entry in scanned_data_instances_at_particular_time:
                    donates = entry.troops_donated_monthly
                    received = entry.troops_received_monthly
                    attacks = entry.attacks_won
                    defenses = entry.defenses_won
                    # if donates < 100 and received < 100 and attacks < 5 and defenses < 5:
                    if donates < 100 and received < 100:
                        # this is probably a new season
                        new_season_vote += 1

                number_of_members_at_this_time = len(scanned_data_instances_at_particular_time)

                if (new_season_vote / number_of_members_at_this_time) > .90:
                    # looks like a new season!!

                    possible_updated_start_timestamp = timestamp

                    # this is where the reset should be
                    if season_start_time < possible_updated_start_timestamp < season_end_time:
                        print('this season seems to reset at the right time')
                        # nothing to do
                    else:
                        print('this season seems to reset before: {}'.format(possible_updated_start_timestamp))

                        possible_updated_end_timestamp_for_previous_season = previous_timestamp

                        # if I want to find when it actually reset, if there is only one top of the hour in between these times, it's almost defintely there...
                        midpoint = int((possible_updated_end_timestamp_for_previous_season + possible_updated_start_timestamp) / 2)
                        new_end = midpoint - 1
                        new_start = midpoint

                        season_instance.start_time = new_start
                        prev_instance.end_time = new_end

                    break
                previous_timestamp = timestamp
            prev_instance = season_instance

    def process_season_historical_data(self, clan_tag_to_scan=None):

        if clan_tag_to_scan is None:
            clan_tag_to_scan = self.clan_tag_to_scan

        member_query = self.session.query(MEMBER)
        season_query = self.session.query(SEASON)

        full_run = False
        if self.initial_run:
            full_run = True
            print('performing full run')

        if not full_run:

            last_season_instance = self.session.query(SEASON) \
                .filter(SEASON.start_time <= self.previous_processed_time) \
                .filter(SEASON.end_time >= self.previous_processed_time).one_or_none()
            if last_season_instance is None:
                raise Exception("Why are you asking for this time? No season matches it.")

            season_query = season_query.filter(SEASON.season_id >= last_season_instance.season_id)

            if clan_tag_to_scan is not None:
                member_query = member_query.filter(MEMBER.clan_tag == clan_tag_to_scan)

        member_instances = member_query.all()
        season_instances = season_query.all()

        for season_instance in season_instances:
            print('processing a season: {}'.format(season_instance.season_id))
            season_start_time = season_instance.start_time
            season_end_time = season_instance.end_time

            for member_instance in member_instances:

                debug = False
                if debug:
                    print('processing member: {}'.format(member_instance.member_tag))

                # get all datapoints for them that fall within the season times
                # all_scanned_data = member_instance.get_all_scanned_data_between_timestamps(season_start_time, season_end_time)
                all_scanned_data = self.session.query(SCANNEDDATA) \
                    .filter(SCANNEDDATA.member_tag == member_instance.member_tag) \
                    .filter(SCANNEDDATA.timestamp >= season_start_time) \
                    .filter(SCANNEDDATA.timestamp <= season_end_time).all()
                if len(all_scanned_data) == 0:
                    # this member wasn't here during this period
                    continue
                elif len(all_scanned_data) == 1:
                    scanned_data_instance = all_scanned_data[0]
                    total_troops_donated = scanned_data_instance.troops_donated_monthly
                    total_troops_received = scanned_data_instance.troops_received_monthly
                    attacks_won = scanned_data_instance.attacks_won
                    defenses_won = scanned_data_instance.defenses_won
                    total_spells_donated = None
                else:
                    total_troops_donated = 0
                    total_troops_received = 0
                    current_iteration_donated = 0
                    current_iteration_received = 0
                    for scanned_data_instance in all_scanned_data:
                        if debug:
                            print(scanned_data_instance)
                        # the attack and win values are used since we only want the last value after the loop
                        troops_donated = scanned_data_instance.troops_donated_monthly
                        troops_received = scanned_data_instance.troops_received_monthly
                        attacks_won = scanned_data_instance.attacks_won
                        defenses_won = scanned_data_instance.defenses_won
                        if troops_donated < current_iteration_donated or troops_received < current_iteration_received:
                            total_troops_donated += current_iteration_donated
                            total_troops_received += current_iteration_received
                        current_iteration_donated = troops_donated
                        current_iteration_received = troops_received
                    total_troops_donated += current_iteration_donated
                    total_troops_received += current_iteration_received

                    total_spells_donated = None
                    initial_spells_donated = all_scanned_data[0].spells_donated_achievement
                    final_spells_donated = all_scanned_data[-1].spells_donated_achievement
                    if initial_spells_donated is not None and final_spells_donated is not None:
                        total_spells_donated = final_spells_donated - initial_spells_donated
                    total_troops_donated -= total_spells_donated

                season_historical_data_instance = self.session.query(SEASONHISTORICALDATA) \
                    .filter(SEASONHISTORICALDATA.season_id == season_instance.season_id) \
                    .filter(SEASONHISTORICALDATA.member_tag == member_instance.member_tag).one_or_none()
                if season_historical_data_instance is None:
                    calculation_to_add = SEASONHISTORICALDATA(season=season_instance,
                                                              member_tag=member_instance.member_tag
                                                              )
                    calculation_to_add.troops_donated = total_troops_donated
                    calculation_to_add.troops_received = total_troops_received
                    calculation_to_add.spells_donated = total_spells_donated
                    calculation_to_add.attacks_won = attacks_won
                    calculation_to_add.defenses_won = defenses_won
                    self.session.add(calculation_to_add)
                else:
                    season_historical_data_instance.troops_donated = total_troops_donated
                    season_historical_data_instance.troops_received = total_troops_received
                    season_historical_data_instance.spells_donated = total_spells_donated
                    season_historical_data_instance.attacks_won = attacks_won
                    season_historical_data_instance.defenses_won = defenses_won
            print('done processing season')

    def get_min_allowable_time_for_clan_game_data(self, current_games_id):
        """
        This calculates the valid timestamp for the minimum acceptable value for clan games data
        :param current_games_id:
        :return:
        """
        clan_game_data = self.session.query(CLANGAME).all()
        result = -1
        if current_games_id == 0:
            result = 0
        else:
            for clan_game in clan_game_data:
                id_of_games_in_loop = clan_game.clan_games_id
                if id_of_games_in_loop == current_games_id - 1:
                    result = clan_game.end_time + 1
        return result

    def get_max_allowable_time_for_clan_game_data(self, current_games_id):
        """
        This calculates the valid timestamp for the maximum acceptable value for clan games data
        :param current_games_id:
        :return:
        """
        clan_game_data = self.session.query(CLANGAME).all()
        result = -1
        if current_games_id == 0:
            result = 0
        else:
            last_clan_game = clan_game_data[-1]
            if last_clan_game.clan_games_id == current_games_id:
                return -2
            for clan_game in clan_game_data:
                if clan_game.clan_games_id == current_games_id + 1:
                    result = clan_game.start_time - 1
        return result

    def process_clan_games_data(self, clan_tag_to_scan=None):

        if clan_tag_to_scan is None:
            clan_tag_to_scan = self.clan_tag_to_scan

        # todo
        # automate clan games start and end time detection
        # bring in the borders of this to first scan before and after clan games started
        # stop it from scanning all clan games

        clan_games_query = self.session.query(CLANGAME)
        member_query = self.session.query(MEMBER)

        full_run = False
        if self.initial_run:
            full_run = True
            print('performing full run')

        if not full_run:
            clan_games_query = clan_games_query.filter(CLANGAME.end_time > self.previous_processed_time)
            if clan_tag_to_scan is not None:
                member_query = member_query.filter(MEMBER.clan_tag == clan_tag_to_scan)

        clan_games_query = clan_games_query.filter(CLANGAME.start_time <= DateFetcherFormatter.get_utc_timestamp())

        clan_games_instances = clan_games_query.all()
        member_instances = member_query.all()

        for clan_games_instance in clan_games_instances:

            # scanned data has millisecond precision, should probably change that
            clan_game_start_time = clan_games_instance.start_time
            clan_game_end_time = clan_games_instance.end_time
            clan_game_id = clan_games_instance.clan_games_id

            print("Processing clan games #: " + str(clan_game_id))

            min_allowable_time_for_clan_game_data = self.get_min_allowable_time_for_clan_game_data(clan_game_id)
            max_allowable_time_for_clan_game_data = self.get_max_allowable_time_for_clan_game_data(clan_game_id)

            for member_instance in member_instances:

                all_scanned_data_relevant_to_clan_game_for_member_query = self.session.query(SCANNEDDATA) \
                    .filter(SCANNEDDATA.member_tag == member_instance.member_tag) \
                    .filter(SCANNEDDATA.timestamp >= min_allowable_time_for_clan_game_data)

                if max_allowable_time_for_clan_game_data != -2:
                    all_scanned_data_relevant_to_clan_game_for_member_query = all_scanned_data_relevant_to_clan_game_for_member_query \
                        .filter(SCANNEDDATA.timestamp <= max_allowable_time_for_clan_game_data)

                all_scanned_data_relevant_to_clan_game_for_member = all_scanned_data_relevant_to_clan_game_for_member_query.all()

                if len(all_scanned_data_relevant_to_clan_game_for_member) == 0:
                    continue
                elif len(all_scanned_data_relevant_to_clan_game_for_member) == 1:
                    continue

                first_points = all_scanned_data_relevant_to_clan_game_for_member[0].clan_games_points_achievement
                last_points = all_scanned_data_relevant_to_clan_game_for_member[-1].clan_games_points_achievement
                points_scored = last_points - first_points

                clan_games_score_instance = self.session.query(CLANGAMESSCORE) \
                    .filter(CLANGAMESSCORE.member_tag == member_instance.member_tag) \
                    .filter(CLANGAMESSCORE.clan_games_id == clan_games_instance.clan_games_id).one_or_none()

                if clan_games_score_instance:
                    clan_games_score_instance.score = points_scored
                else:
                    clan_games_score_to_add = CLANGAMESSCORE()
                    clan_games_score_to_add.member = member_instance
                    clan_games_score_to_add.score = points_scored
                    clan_games_score_to_add.clan_game = clan_games_instance
                    self.session.add(clan_games_score_to_add)

    def mark_successful_save(self):
        # todo make this the last data time instead of when we processed
        time_to_set = DateFetcherFormatter.get_utc_timestamp()
        previous_processed_time_instance = self.session.query(LASTPROCESSED).filter(LASTPROCESSED.id == 1).one_or_none()
        if previous_processed_time_instance is None:
            previous_processed_time_instance = LASTPROCESSED()
            self.session.add(previous_processed_time_instance)
        previous_processed_time_instance.time = time_to_set
        return time_to_set

    # reading data into database
    def save_data(self):

        # todo - rather than all achievements, then all wars, etc
        # todo - do it chronologically, at least by day, if not by data time

        # this contains all the info about the player
        print('process_player_achievement_files')
        self.process_player_achievement_files()

        # used to also process clan profile, was there actually any benefit that's not
        # covered by the achievement files?

        print('process_clan_war_league_files')
        self.process_clan_war_league_files()

        # this contains details on the current war (at the time of saving)
        print('process_clan_war_details_files')
        self.process_clan_war_details_files()

        print('checking initial stuff')
        if self.initial_run:
            # import certain data
            print('importing linked accounts')
            self.import_linked_accounts_to_db()

            print('importing player data')
            self.import_member_data_to_db()

        print('importing trader shop data')
        self.import_trader_data_to_db()

        print('importing clan games metadata')
        self.import_clan_games_metadata()

        print('populating seasons')
        self.populate_seasons_in_db()

        print('validating seasons')
        self.validate_seasons_in_db()

        print('processing season data')
        self.process_season_historical_data()

        print('processing clan games data')
        self.process_clan_games_data()

        print('marking save successful')
        return self.mark_successful_save()


def init():
    if __name__ == "__main__":
        with session_scope() as session:
            fdp = FetchedDataProcessor(session)
            fdp.save_data()


init()
