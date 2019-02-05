#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
from sqlite3 import Error
import time
import dateutil.parser as dp
import json
import random
import unittest
import pytz
import datetime
import dateutil
import date_fetcher_formatter
import config_strings

from ClashBot import DateFetcherFormatter, session_scope
from ClashBot.models import DISCORDCLASHLINK, MEMBER, WARATTACK, WAR, DISCORDACCOUNT, WARPARTICIPATION, TRADERDATA, TRADERITEM, SCANNEDDATA

from sqlalchemy.sql.expression import func

db_file = "clashData.db"
#currentSeasonIDs = {}


class NoDataDuringTimeSpanException(Exception):
    pass


class NoActiveClanWarLeagueWar(Exception):
    pass


class NoActiveClanWar(Exception):
    pass


class TraderInvalidInput(Exception):
    pass


class TraderAccountNotConfigured(Exception):
    pass


class DatabaseAccessor:

    def __init__(self, session):

        self.session = session

        with open("configs/app.json") as infile:
            app_config = json.load(infile)
            self.my_clan_tag = app_config["my_clan_tag"]

    def get_discord_ids_of_members_who_are_th12(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        discord_clash_links = self.session.query(DISCORDCLASHLINK) \
                    .join(MEMBER) \
                    .filter(MEMBER.town_hall_level == 12) \
                    .filter(MEMBER.clan_tag == clan_tag) \
                    .all()

        actual_results = set()

        for discord_clan_link in discord_clash_links:
            print(discord_clan_link.clash_account.member_name)
            actual_results.add(str(discord_clan_link.discord_tag))

        return actual_results

    def get_today_cwl_war(self):
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.is_clan_war_league_war == 1) \
            .filter(WAR.war_day_start <= current_time) \
            .filter(WAR.war_day_end >= current_time).one_or_none()
        if war_instance is None:
            raise NoActiveClanWarLeagueWar()
        return war_instance

    def get_tomorrow_cwl_war(self):
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.is_clan_war_league_war == 1) \
            .filter(WAR.prep_day_start <= current_time) \
            .filter(WAR.war_day_start >= current_time).one_or_none()
        if war_instance is None:
            raise NoActiveClanWarLeagueWar()
        return war_instance

    def get_cwl_roster_and_war_today(self):
        war_instance = self.get_today_cwl_war()
        return self.session.query(WARPARTICIPATION) \
            .filter(WARPARTICIPATION.war == war_instance).all(), war_instance

    def get_cwl_roster_and_war_tomorrow(self):
        war_instance = self.get_tomorrow_cwl_war()
        return self.session.query(WARPARTICIPATION) \
            .filter(WARPARTICIPATION.war == war_instance).all(), war_instance

    def is_today_cwl_roster_complete(self):
        roster, _ = self.get_cwl_roster_and_war_today()
        return len(roster) == 15

    def is_tomorrow_cwl_roster_complete(self):
        roster, _ = self.get_cwl_roster_and_war_tomorrow()
        return len(roster) == 15

    def add_member_to_cwl(self, member_instance, war_instance):
        # todo this data should be added to the exporter
        war_participation_instance = WARPARTICIPATION()
        war_participation_instance.war = war_instance
        war_participation_instance.member = member_instance
        # 2 means we think
        war_participation_instance.is_clan_war_league_war = 2
        attack_1_instance = WARATTACK()
        attack_1_instance.attacker_attack_number = 1
        attack_1_instance.war = war_instance
        attack_1_instance.member = member_instance
        attack_1_instance.attacker_tag = member_instance.member_tag
        war_participation_instance.attack1 = attack_1_instance
        self.session.add(war_participation_instance)

    def remove_member_from_current_cwl(self, member_instance, war_instance):
        for war_participation_instance in war_instance.war_participations:
            if war_participation_instance.member == member_instance:
                self.session.delete(war_participation_instance)
                break

    def get_members_in_clan_with_name(self, member_name, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        return self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag) \
            .filter(func.upper(MEMBER.member_name) == member_name).all()

    def get_timestamps_for_current_war(self):

        current_timestamp = DateFetcherFormatter.get_utc_timestamp()

        war_end_time = self.session.query(WAR.war_day_end) \
            .filter(WAR.war_day_start < current_timestamp) \
            .filter(WAR.war_day_end > current_timestamp).scalar()

        if war_end_time is None:
            return None
        else:
            print('make me sort descending please!')
            war_end_time = war_end_time
            hours_remaining_reminder = [6, 5, 4, 3, 2, 1]
            results = []
            for hour_reminder in hours_remaining_reminder:
                this_timestamp = war_end_time - (hour_reminder * 3600)
                if this_timestamp > current_timestamp:
                    time_remaining_string = '{} hours remaining in war!'.format(hour_reminder)
                    if hour_reminder == 1:
                        time_remaining_string = '{} hour remaining in war!'.format(hour_reminder)
                    results.append((this_timestamp, time_remaining_string))
            if len(results) == 0:
                return None
            else:
                return results

    def get_members_in_war_with_attacks_remaining(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        current_time = DateFetcherFormatter.get_utc_timestamp()
        current_war = self.session.query(WAR) \
            .filter(WAR.friendly_tag == clan_tag) \
            .filter(WAR.war_day_start < current_time) \
            .filter(WAR.war_day_end > current_time).one_or_none()

        if current_war is None:
            raise NoActiveClanWar()
        else:
            results = {
                "discord": {},
                "no_discord": []
            }
            for war_participation in current_war.war_participations:
                member = war_participation.member

                attacks_remaining = 0
                # is standard war
                if war_participation.is_clan_war_league_war == 0:
                    if war_participation.attack1.stars is None:
                        attacks_remaining = 2
                    elif war_participation.attack2.stars is None:
                        attacks_remaining = 1
                else:
                    if war_participation.attack1.stars is None:
                        attacks_remaining = 1

                if attacks_remaining != 0:
                    these_results = {
                        "member_name": member.member_name,
                        "attacks_remaining": attacks_remaining
                    }
                    if len(member.discord_clash_links) == 0:
                        results["no_discord"].append(these_results)
                    for discord_clash_link in member.discord_clash_links:
                        discord_id = discord_clash_link.discord_tag
                        if discord_id not in results["discord"]:
                            results["discord"][discord_id] = []
                        results["discord"][discord_id].append(these_results)
            return results

    def link_discord_account(self, discord_identifier, clash_identifier, is_name=False):

        print(clash_identifier)
        print(is_name)

        member_query = self.session.query(MEMBER)
        if is_name:
            member_query = member_query.filter(func.upper(MEMBER.member_name) == clash_identifier)
        else:
            # tag
            member_query = member_query.filter(MEMBER.member_tag == clash_identifier)

        member_instances = member_query.all()

        if len(member_instances) == 0:
            return config_strings.unable_to_find_account_string

        if len(member_instances) > 1:
            print('Multiple accounts matched while linking, better fix this')

        member_instance = member_instances[0]

        discord_account_instance = self.session.query(DISCORDACCOUNT)\
            .filter(DISCORDACCOUNT.discord_tag == discord_identifier).one_or_none()

        if discord_account_instance is None:
            discord_account_instance = DISCORDACCOUNT()
            discord_account_instance.is_troop_donator = -1
            discord_account_instance.discord_tag = discord_identifier
            discord_account_instance.has_permission_to_set_war_status = False
            discord_account_instance.time_last_checked_in = DateFetcherFormatter.get_utc_timestamp()
            # 12 am utc, which is right after the shop changes
            discord_account_instance.trader_shop_reminder_hour = 0

        for clash_links in discord_account_instance.discord_clash_links:
            if clash_links.clash_account == member_instance:
                print('This account is already linked, should change this :)')
                return config_strings.successfully_linked_string

        discord_clash_link = DISCORDCLASHLINK()
        discord_clash_link.discord_account = discord_account_instance
        discord_clash_link.clash_account = member_instance
        discord_clash_link.account_order = len(discord_account_instance.discord_clash_links) + 1

        self.session.add(discord_account_instance)

        return config_strings.successfully_linked_string

    def has_linked_account_with_th_larger_than(self, discord_id, th_level_to_check_for):

        accounts = self.session.query(MEMBER) \
                            .join(DISCORDCLASHLINK) \
                            .filter(DISCORDCLASHLINK.discord_tag == discord_id) \
                            .filter(MEMBER.town_hall_level > th_level_to_check_for) \
                            .all()

        return len(accounts) > 0

    def has_configured_is_troop_donator(self, discord_id):

        result = self.session.query(DISCORDACCOUNT.is_troop_donator) \
                .filter(DISCORDACCOUNT.discord_tag == discord_id) \
                .one_or_none()

        if result == -1:
            return  False
        return True

    def get_members_in_clan(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        results = self.session.query(DISCORDACCOUNT) \
                                    .join(DISCORDCLASHLINK) \
                                    .join(MEMBER) \
                                    .filter(MEMBER.clan_tag == clan_tag) \
                                    .all()

        actual_results = {}

        for discord_account in results:
            is_troop_donator = 0
            if discord_account.is_troop_donator == 1:
                is_troop_donator = 1
            actual_results[str(discord_account.discord_tag)] = is_troop_donator

        return actual_results

    def get_discord_members_in_war(self):
        # find the active war day, if there is one
        current_time = DateFetcherFormatter.get_utc_timestamp()
        war_instance = self.session.query(WAR) \
            .filter(WAR.war_day_start <= current_time) \
            .filter(WAR.war_day_end >= current_time).one_or_none()

        if war_instance is None:
            # find a prep day if there is no active war day
            war_instance = self.session.query(WAR) \
                .filter(WAR.prep_day_start <= current_time) \
                .filter(WAR.war_day_start >= current_time).one_or_none()

        # if no prep day, we aren't in war at all
        if war_instance is None:
            raise NoActiveClanWar()

        war_particips = self.session.query(WARPARTICIPATION).filter(WARPARTICIPATION.war == war_instance).all()

        clash_account_numbers = set()

        for war_particip in war_particips:
            member = war_particip.member
            for discord_clash_link in member.discord_clash_links:
                clash_account_numbers.add(str(discord_clash_link.discord_tag))

        return clash_account_numbers

    def get_discord_ids_of_members_with_war_permissions(self):
        results = self.session.query(DISCORDACCOUNT) \
            .filter(DISCORDACCOUNT.has_permission_to_set_war_status == 1) \
            .all()

        actual_results = set()

        for discord_account in results:
            actual_results.add(str(discord_account.discord_tag))

        return actual_results

    def get_all_members_without_discord_as_string(self):
        result_list = self.get_all_members_without_discord()
        result_string = ""
        for entry in result_list:
            result_string += entry + '\n'
        return result_string

    def get_all_members_without_discord(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        members_in_clan = self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag).all()

        actual_results = []
        for member in members_in_clan:
            if len(member.discord_clash_links) == 0:
                actual_results.append(member.member_name)

        return actual_results

    def get_members_by_offensive_score(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        # implement this?
        all_members_in_clan = self.session.query(MEMBER).filter(MEMBER.clan_tag == clan_tag).all()

        return all_members_in_clan
        # scores = {}
        # for member in all_members_in_clan:
        #     member_score = member.town_hall_level*3
        #     member_score += member.king_level
        #     member_score += member.queen_level
        #     member_score += member.warden_level
        #     season_historical_data_instance = member.season_historical_data[-1]
        #     member_score += int(season_historical_data_instance.troops_donated / 10)
        #     member_score += season_historical_data_instance.attacks_won
        #     if member_score not in scores:
        #         scores[member_score] = []
        #     scores[member_score].append(member)
        #
        # counter = 1
        # for score in sorted(scores, reverse=True):
        #     for member in scores[score]:
        #         season_historical_data_instance = member.season_historical_data[-1]
        #         print('{}) {}:'.format(counter, member.member_name))
        #         print('    TH   : {}'.format(member.town_hall_level))
        #         print('    King : {}'.format(member.king_level))
        #         print('    Queen: {}'.format(member.queen_level))
        #         print('    GW   : {}'.format(member.warden_level))
        #         print('    Donat: {}'.format(season_historical_data_instance.troops_donated))
        #         print('    Attac: {}'.format(season_historical_data_instance.attacks_won))
        #         counter += 1
        #         pass

    def get_trader_current_day_no_offset(self):
        # get the time used for the calculations
        base_day_timestamp = self.session.query(TRADERDATA.value).filter(TRADERDATA.id==1).scalar()

        # get the trader cycle length
        trader_cycle_length = self.get_trader_cycle_length()

        # determine what the "system" thinks the day is currently
        base_day = datetime.datetime.utcfromtimestamp(base_day_timestamp).replace(tzinfo=pytz.utc)
        current_cycle_no_offset_timedelta = DateFetcherFormatter.get_utc_date_time() - base_day
        # get the current trader day in the cycle, and make it 1 indexed
        current_cycle_no_offset = (current_cycle_no_offset_timedelta.days % trader_cycle_length) + 1

        print(current_cycle_no_offset)
        print(trader_cycle_length)
        return current_cycle_no_offset, trader_cycle_length

    def get_trader_cycle_length(self):
        return self.session.query(TRADERDATA.value).filter(TRADERDATA.id==2).scalar()

    def set_trader_time_for_discord_id(self, discord_id, hour):
        discord_instance = self.session.query(DISCORDACCOUNT).filter(DISCORDACCOUNT.discord_tag==discord_id).one()
        discord_instance.trader_shop_reminder_hour = hour

    def set_trader_day_for_member(self, member_instance, current_trader_day):
        """

        :param member_instance:
        :param current_trader_day: Comes in 1-indexed
        :return:
        """

        current_cycle_no_offset, trader_cycle_length = self.get_trader_current_day_no_offset()

        if current_trader_day <= 0 or current_trader_day > trader_cycle_length:
            raise TraderInvalidInput

        if current_trader_day < current_cycle_no_offset:
            current_trader_day += trader_cycle_length
        calculated_offset = current_trader_day - current_cycle_no_offset
        member_instance.trader_rotation_offset = calculated_offset

    def get_trader_day_for_member(self, member_instance):

        current_cycle_no_offset, trader_cycle_length = self.get_trader_current_day_no_offset()

        member_offset = member_instance.trader_rotation_offset

        if member_offset is None:
            raise TraderAccountNotConfigured

        # find the members day
        calculated_day = member_offset + current_cycle_no_offset
        if calculated_day > trader_cycle_length:
            calculated_day = calculated_day - trader_cycle_length
        return calculated_day

    def get_accounts_who_get_trader_reminders(self, now_only=True):

        print("get_accounts_who_get_trader_reminders running")

        # get accounts with notifications at this time
        dt = DateFetcherFormatter.get_utc_date_time()
        hour = dt.hour
        print("current_hour: {}".format(hour))
        if now_only:
            accounts_who_want_reminders = self.session.query(DISCORDACCOUNT).filter(DISCORDACCOUNT.trader_shop_reminder_hour == hour).all()
        else:
            accounts_who_want_reminders = self.session.query(DISCORDACCOUNT).all()

        # generate list of all items
        current_trader_rotation = {}
        current_items = self.session.query(TRADERITEM).all()
        for item_instance in current_items:
            item_day_in_rotation = int(item_instance.day_in_rotation)
            if item_day_in_rotation not in current_trader_rotation:
                current_trader_rotation[item_day_in_rotation] = []
            current_trader_rotation[item_day_in_rotation].append(item_instance)

        # todo, add filtering in the case of enabling or disabling on a per clash account basis

        # get the current day
        current_cycle_no_offset, trader_cycle_length = self.get_trader_current_day_no_offset()
        results = {}

        # get the day for each account
        for discord_account_instance in accounts_who_want_reminders:
            for discord_clash_link in discord_account_instance.discord_clash_links:
                clash_account = discord_clash_link.clash_account
                if clash_account.trader_rotation_offset is None:
                    continue

                # check to see if each account has items on this day
                clash_account_trader_day = current_cycle_no_offset + clash_account.trader_rotation_offset
                if clash_account_trader_day > trader_cycle_length:
                    clash_account_trader_day = clash_account_trader_day - trader_cycle_length

                print("{} is on day {}".format(clash_account.member_name, clash_account_trader_day))

                if clash_account_trader_day in current_trader_rotation:
                    for item in current_trader_rotation[clash_account_trader_day]:
                        if discord_account_instance.discord_tag not in results:
                            results[discord_account_instance.discord_tag] = {}
                        if clash_account.member_name not in results[discord_account_instance.discord_tag]:
                            results[discord_account_instance.discord_tag][clash_account.member_name] = []
                        cost_string = item.name + " for "
                        if item.cost == 0:
                            cost_string += "FREE"
                        else:
                            cost_string += "{} gems".format(item.cost)
                        results[discord_account_instance.discord_tag][clash_account.member_name].append(cost_string)

        return results

    def get_trader_cycle_url(self):
        # todo load this into db
        return "https://www.reddit.com/r/ClashOfClans/comments/a5hx4z/misc_trader_cycle_after_the_december_2018_update/"

    def get_discord_account(self, discord_id):
        return self.session.query(DISCORDACCOUNT).filter(DISCORDACCOUNT.discord_tag == discord_id).one()

    def get_linked_accounts(self, discord_id, clan_tag=None, currently_in_clan_only=False):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        query = self.session.query(MEMBER) \
            .join(DISCORDCLASHLINK) \
            .join(DISCORDACCOUNT) \
            .filter(DISCORDACCOUNT.discord_tag == discord_id)
        if currently_in_clan_only:
            query = query.filter(MEMBER.clan_tag==clan_tag)
        account_list = query.all()
        return account_list

    def get_donations_for_x_days(self, num_days, clan_tag=None):
        if clan_tag is None:
            clan_tag = self.my_clan_tag

        members_in_clan = self.session.query(MEMBER).filter(MEMBER.clan_tag == clan_tag).all()
        results = {}
        timestamp_to_get_donations_since = (DateFetcherFormatter.get_utc_date_time() - datetime.timedelta(days=num_days)).timestamp()
        # last_week_timestamp = 0
        max_y = 0
        max_diff = 0
        min_x = DateFetcherFormatter.get_utc_timestamp()
        max_x = 0
        for member in members_in_clan:
            data = self.get_donations_since_time_for_member(member, timestamp_to_get_donations_since)

            if len(data) == 0:
                print("skipping")
                continue

            results[member.member_name] = data

            for datapoint in data:
                if datapoint[1] > max_y:
                    max_y = datapoint[1]

            if data[0][0] < min_x:
                min_x = data[0][0]
            if data[0][0] > max_x:
                max_x = data[0][0]
        return {
            "results": results,
            "starting_timestamp": timestamp_to_get_donations_since,
            "min_x": min_x,
            "max_x": max_x,
            "min_y": 0,
            "max_y": max_y
        }

    def get_donations_since_time_for_member(self, member_instance, timestamp):

        results = self.session.query(SCANNEDDATA) \
            .join(MEMBER) \
            .filter(MEMBER.member_tag == member_instance.member_tag) \
            .filter(SCANNEDDATA.timestamp > timestamp) \
            .all()

        # culmulative
        # initial_datapoint = results[0].troops_donated_achievement
        # results = [(x.timestamp, (x.troops_donated_achievement - initial_datapoint)) for x in results]
        # return results

        # diff
        new_results = []
        prev_value = None
        prev_time = None
        for entry in results:
            if prev_value is None:
                prev_value = entry.troops_donated_achievement
                prev_time = entry.timestamp
            elif entry.timestamp - prev_time > (6 * 60 * 60):
                # if data spans more than 6 hours, skip it
                prev_value = entry.troops_donated_achievement
                prev_time = entry.timestamp
            else:
                val = entry.troops_donated_achievement - prev_value
                new_results.append((entry.timestamp, val))
                prev_value = entry.troops_donated_achievement
        return new_results

    def get_all_donated_or_received_in_time_frame(self, time_created, time_finished, clan_tag=None):

        results = self.get_all_donated_or_received_in_time_frame_raw(time_created, time_finished, clan_tag)

        if 'error' in results:
            return results['error']

        standard = results['standard']
        left_since_created = results['left_since_created']
        joined_since_created = results['joined_since_created']
        if len(standard) == 0 and len(left_since_created) == 0 and len(joined_since_created) == 0:
            return "No-one seems to have donated in that timeframe that fits these requirements"

        results_string = ""
        if len(standard) > 0:
            results_string += "These members donated the following amounts during this timeframe:\n"
            for entry in standard:
                results_string += "{}: {}\n".format(entry["name"], entry["donated"])
        if len(joined_since_created) > 0:
            results_string += "These members donated the following amounts during this timeframe (and are new members):\n"
            for entry in joined_since_created:
                results_string += "{}: {}\n".format(entry["name"], entry["donated"])
        if len(left_since_created) > 0:
            results_string += "These members left after the request was created so they may also have been responsible for filling it::\n"
            for entry in left_since_created:
                results_string += "{}: {}\n".format(entry["name"], entry["donated"])

        return results_string

    def get_all_donated_or_received_in_time_frame_raw(self, time_created, time_finished, clan_tag=None):
        if clan_tag is None:
            clan_tag = self.my_clan_tag

        result_dict = {
            'left_since_created': [],
            'standard': [],
            'joined_since_created': [],
            'debug': [time_created, time_finished]
        }

        members_in_clan = self.session.query(MEMBER).filter(MEMBER.clan_tag == clan_tag).all()
        for member in members_in_clan:
            member_joined_after_request_created = False
            member_left_after_request_created = False

            donations_before = self.session.query(SCANNEDDATA) \
                .filter(SCANNEDDATA.member_tag == member.member_tag) \
                .filter(SCANNEDDATA.timestamp <= time_created) \
                .order_by(SCANNEDDATA.timestamp.desc()) \
                .first()

            if donations_before is None:
                # this is when the member just joined
                member_joined_after_request_created = True

            donations_after = self.session.query(SCANNEDDATA) \
                .filter(SCANNEDDATA.member_tag == member.member_tag) \
                .filter(SCANNEDDATA.timestamp >= time_finished) \
                .order_by(SCANNEDDATA.timestamp.asc()) \
                .first()

            if donations_after is None:
                # the member just left
                member_left_after_request_created = True

            if member_joined_after_request_created and member_left_after_request_created:
                print('whats happening')
                result_dict['error'] = 'error 3'
                return result_dict
            elif member_joined_after_request_created:
                entry = {
                    'tag':  member.member_tag,
                    'name':  member.member_name,
                    'donated':  donations_after.troops_donated_monthly,
                    'received':  donations_after.troops_received_monthly
                }
                result_dict['joined_since_created'].append(entry)
            elif member_left_after_request_created:
                entry = {
                    'tag':  member.member_tag,
                    'name':  member.member_name,
                    'donated':  '?',
                    'received':  '?'
                }
                result_dict['left_since_created'].append(entry)
            else:
                donated_before_num = donations_before.troops_donated_monthly
                donated_after_num = donations_after.troops_donated_monthly
                donated = donated_after_num - donated_before_num

                received_before_num = donations_before.troops_received_monthly
                received_after_num = donations_after.troops_received_monthly
                received = received_after_num - received_before_num

                if donated != 0 or received != 0:
                    entry = {
                        'tag':  member.member_tag,
                        'name':  member.member_name,
                        'donated':  donated,
                        'received':  received
                    }
                    result_dict['standard'].append(entry)

        return result_dict


def getCursorAndConnection():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return cursor, conn


def getLastProcessedTime():
    cursor, conn = getCursorAndConnection()
    query = '''
	SELECT time
		FROM
			LAST_PROCESSED
		WHERE
			COUNT = 1
		'''
    cursor.execute(query)
    result = cursor.fetchone()
    if result == None:
        result = 0
    else:
        result = result[0]
    conn.close()
    return result


def getSeasonIdForTimestamp(timestamp):
    cursor, conn = getCursorAndConnection()
    query = '''
	SELECT season_id
		FROM
			SEASONS
		WHERE
			start_time <= ? and end_time >= ?
		'''
    cursor.execute(query, (timestamp, timestamp))
    result = cursor.fetchone()
    if result == None:
        result = None
    else:
        result = result[0]
    conn.close()
    return result


def getAllMembersTagSupposedlyInClan(cursor):
    cursor.execute(
        '''
		SELECT member_tag FROM
			MEMBERS
		WHERE
			in_clan_currently = 1
		'''
    )
    return cursor.fetchall()

def removeDiscordAccountsRelatedTo(accountName):
    cursor, conn = getCursorAndConnection()
    changed = 0

    query = '''SELECT discord_tag FROM discord_clash_links WHERE member_tag = (
			SELECT member_tag FROM MEMBERS WHERE UPPER(member_name) = ?
			)
		'''
    cursor.execute(query, (accountName,))
    discord_tags = cursor.fetchall()
    for discord_tag in discord_tags:
        discord_tag = discord_tag[0]
        query = '''DELETE FROM discord_clash_links WHERE discord_tag = ?'''
        cursor.execute(query, (discord_tag, ))
        changed += cursor.rowcount
        query = '''DELETE FROM discord_properties WHERE discord_tag = ?'''
        cursor.execute(query, (discord_tag, ))
        changed += cursor.rowcount
    conn.commit()
    conn.close()
    return changed


def getMembersFromLastWar():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()

    query = '''
		SELECT member_name 
		FROM
		MEMBERS where in_clan_currently = 1
		ORDER BY trophies DESC
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersList = []
    for entry in data:
        membersList.append(entry[0])

    cursor.execute(
        '''
		SELECT mems.member_name 
		FROM MEMBERS mems			
		INNER JOIN WAR_ATTACKS war_attacks
			ON war_attacks.attacker_tag = mems.member_tag
		INNER JOIN WARS wars
			ON wars.war_id = war_attacks.war_id
		WHERE
			wars.war_id = (SELECT MAX(war_id) FROM WARS)
			AND
			war_attacks.attacker_attack_number = 1
		ORDER BY mems.trophies DESC;
		'''
    )
    data = cursor.fetchall()
    conn.close()
    result = ""
    for entry in data:
        if entry[0] in membersList:
            result += str(membersList.index(entry[0]
                                            ) + 1) + ") " + entry[0] + "\n"
        else:
            result += "*X) " + entry[0] + "*\n"
    return result


def getNewWarRoster():
    try:
        val = getNewWarRoster2()
        print(val)
        return val
    except:
        print("Unexpected error:", sys.exc_info()[0])


def getNewWarRoster2():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()

    cursor, conn = getCursorAndConnection()

    query = '''
		SELECT member_name 
		FROM
		MEMBERS where in_clan_currently = 1
		ORDER BY trophies DESC
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersList = []
    for entry in data:
        membersList.append(entry[0])

    query = '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		INNER JOIN ADD_TO_WAR
			ON MEMBERS.member_tag = ADD_TO_WAR.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    membersToAdd = []
    if len(data) != 0:
        for entry in data:
            memberName = entry[0]
            if memberName in membersList:
                membersToAdd.append(memberName)

    print('adding these members to war: {}'.format(membersToAdd))

    query = '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		INNER JOIN REMOVE_FROM_WAR
			ON MEMBERS.member_tag = REMOVE_FROM_WAR.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    membersToRemove = []
    if len(data) != 0:
        for entry in data:
            memberName = entry[0]
            if memberName in membersList:
                membersToRemove.append(memberName)

    print('removing these members from war: {}'.format(membersToRemove))

    cursor.execute(
        '''
		SELECT mems.member_name 
		FROM MEMBERS mems			
		INNER JOIN WAR_ATTACKS war_attacks
			ON war_attacks.attacker_tag = mems.member_tag
		INNER JOIN WARS wars
			ON wars.war_id = war_attacks.war_id
		WHERE
			wars.war_id = (SELECT MAX(war_id) FROM WARS)
			AND
			war_attacks.attacker_attack_number = 1
		ORDER BY mems.trophies DESC;
		'''
    )
    data = cursor.fetchall()

    roster = []
    for entry in data:
        memberName = entry[0]
        if memberName in membersList:
            if not memberName in membersToRemove:
                roster.append(memberName)

    for memberName in membersToAdd:
        if memberName in membersList and not memberName in roster:
            roster.append(memberName)

    query = '''
		select war_size from wars where war_id = (select max(war_id) from wars)
		'''
    cursor.execute(query)
    warSize = cursor.fetchone()[0]

    print(warSize)
    origWarSize = warSize
    while len(roster) > warSize:
        warSize += 5

    while len(roster) + 5 <= warSize:
        warSize -= 5
    print(warSize)

    warSizeString = ""
    if warSize != origWarSize:
        warSizeString = "\n\nNote: changed war size from {} to {}".format(
            origWarSize, warSize)
    addedToFillString = ""

    if len(roster) < warSize:
        print('got here')
        query = '''
			SELECT MEMBERS.member_name
			FROM MEMBERS
			WHERE
				in_clan_currently = 1
			AND
				town_hall_level IS NOT NULL
			ORDER BY town_hall_level ASC
			'''
        cursor.execute(query)
        results = cursor.fetchall()
        print('results were')
        print(results)
        for result in results:
            name = result[0]
            if not name in roster:
                if addedToFillString == "":
                    addedToFillString = "\n\nNote: added these to fill roster:\n"
                print('adding to fill roster: {}'.format(name))
                addedToFillString += name + '\n'
                roster.append(name)
            if len(roster) == warSize:
                break

    result = ""
    print(len(roster))
    for i in range(0, len(membersList)):
        memberName = membersList[i]
        if memberName in roster:
            if memberName in addedToFillString:
                result += str(i+1) + ") *" + memberName + "*\n"
            else:
                result += str(i+1) + ") " + memberName + "\n"

    conn.close()
    return result + addedToFillString + warSizeString


def addMemberToWar(member_name):
    #conn = sqlite3.connect(db_file)
    # print(sqlite3.version)
    #cursor = conn.cursor()
    member_name = member_name.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		INSERT OR REPLACE INTO 
			ADD_TO_WAR (member_tag, time_requested, change_number)
		VALUES
			((SELECT member_tag from MEMBERS WHERE upper(member_name) = ?), ?, ?)
		'''
    timestamp = getDataFromServer.get_utc_timestamp()
    result = config_strings.success
    print(member_name)
    try:
        cursor.execute(query, (member_name, timestamp,
                               getMaxRosterChangeNumber(cursor, conn)+1))
    except sqlite3.IntegrityError as e:
        print(e)
        result = config_strings.failed
    conn.commit()
    conn.close()
    return result


def removeMemberFromWar(member_name):
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    member_name = member_name.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		INSERT OR REPLACE INTO 
			REMOVE_FROM_WAR (member_tag, time_requested, change_number)
		VALUES
			((SELECT member_tag from MEMBERS WHERE upper(member_name) = ?), ?, ?)
		'''
    timestamp = getDataFromServer.get_utc_timestamp()
    result = config_strings.success
    try:
        cursor.execute(query, (member_name, timestamp,
                               getMaxRosterChangeNumber(cursor, conn)+1))
    except sqlite3.IntegrityError as e:
        result = config_strings.failed
    conn.commit()
    conn.close()
    return result


def clearAddAndRemoveFromWar():
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()
    query = '''
		DELETE FROM ADD_TO_WAR
		'''
    cursor.execute(query)
    query = '''
		DELETE FROM REMOVE_FROM_WAR
		'''
    cursor.execute(query)
    conn.commit()
    conn.close()


def getMaxRosterChangeNumber(cursor, conn):
    result = 0
    query = '''
		SELECT MAX(change_number) FROM ADD_TO_WAR
		'''
    cursor.execute(query)
    returnedValAdd = cursor.fetchone()[0]
    query = '''
		SELECT MAX(change_number) FROM REMOVE_FROM_WAR
		'''
    cursor.execute(query)
    returnedValRem = cursor.fetchone()[0]
    if returnedValAdd == None:
        if returnedValRem != None:
            result = returnedValRem

    if returnedValRem == None:
        if returnedValAdd != None:
            result = returnedValAdd

    if returnedValRem != None and returnedValAdd != None:
        result = max(returnedValRem, returnedValAdd)

    return result


def getPastWarPerformanceForMemberName(memberName, number_of_wars):
    memberName = memberName.upper()
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT discord_tag FROM discord_clash_links
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_clash_links.member_tag 
		WHERE
			UPPER(MEMBERS.member_name) = UPPER(?)
		'''
    cursor.execute(query, (memberName,))
    discordID = cursor.fetchall()

    print(discordID)

    if len(discordID) == 0:
        query = '''SELECT member_tag, member_name FROM members WHERE UPPER(member_name) = ?'''
        cursor.execute(query, (memberName,))
        results = cursor.fetchall()
        if len(results) == 0:
            raise ValueError('Unable to find this account')
        elif len(results) > 1:
            raise ValueError('Too many accounts with this username...')

        accounts = results[0]
        member_tag_name_dict = {}
        tag = accounts[0]
        name = accounts[1]
        member_tag_name_dict[tag] = name
        return get_past_war_performance_for_member_tags(member_tag_name_dict, number_of_wars)
    else:
        conn.close()
        if len(discordID) > 1:
            raise ValueError(
                'Too many discord ids have accounts with this username...')

        return getPastWarPerformance(discordID[0][0], number_of_wars)


def getPastWarPerformance(discord_id, number_of_wars):
    cursor, conn = getCursorAndConnection()
    # first, get all the tags and member names for every account owned by this discord id
    query = '''
		SELECT members.member_tag, members.member_name FROM MEMBERS
		INNER JOIN DISCORD_CLASH_LINKS ON
		MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
		where DISCORD_CLASH_LINKS.discord_tag = ?
		'''
    account_dict = {}
    cursor.execute(query, (int(discord_id),))
    results = cursor.fetchall()
    for account_data in results:
        tag = account_data[0]
        name = account_data[1]
        account_dict[tag] = name
    print(account_dict)
    conn.close()
    return get_past_war_performance_for_member_tags(account_dict, number_of_wars)


def get_past_war_performance_for_member_tags(member_tag_name_dict, number_of_wars):
    # get the max war id
    # determine if the current war is on going
    # go backwards until we get to the first war or to where we have the total number of desired wars
    cursor, conn = getCursorAndConnection()
    result_dict = {}
    result_dict['wars_participated_in'] = []
    query = """
	    SELECT 
                war_id, result
            FROM
                wars
            WHERE
                war_id = (SELECT MAX(war_id) FROM WARS)
	    """
    cursor.execute(query, ())
    max_war_id, result = cursor.fetchall()[0]
    if result == 'in progress':
        max_war_id = max(0, max_war_id - 1)

    where_clause = ''
    for account_tag in member_tag_name_dict:
        where_clause += "attacker_tag = ? or "
    where_clause = where_clause[:-4]
    where_clause = "(" + where_clause + ")"
    found = 0
    for war_id in range(max_war_id, 1, -1):
        #print('looping')
        query = '''SELECT war_id, attacker_tag, MEMBERS.member_name, attacker_attack_number, attacker_position, defender_position, attacker_town_hall, defender_town_hall, stars, destruction_percentage, attack_occurred_after, attack_occurred_before 
			FROM WAR_ATTACKS 
			INNER JOIN MEMBERS ON WAR_ATTACKS.attacker_tag = MEMBERS.member_tag
			WHERE war_id = ? and '''
        query += where_clause
        vars = [war_id]
        vars.extend(member_tag_name_dict.keys())
#		print(query)
#		print(vars)
        cursor.execute(query, vars)
        results = cursor.fetchall()
        if len(results) > 0:
            dict_for_this_war = {}
            dict_for_this_war['war_attacks'] = []
            for attack in results:
                dict_for_this_attack = {}
                dict_for_this_attack['member_name'] = attack[2]
                dict_for_this_attack['attack_number'] = attack[3]
                dict_for_this_attack['attacker_position'] = attack[4]
                dict_for_this_attack['defender_position'] = attack[5]
                dict_for_this_attack['attacker_town_hall'] = attack[6]
                dict_for_this_attack['defender_town_hall'] = attack[7]
                dict_for_this_attack['stars'] = attack[8]
                dict_for_this_attack['destruction_percentage'] = attack[9]
                dict_for_this_attack['attack_occurred_after'] = attack[10]
                dict_for_this_attack['attack_occurred_before'] = attack[11]
                dict_for_this_war['war_attacks'].append(dict_for_this_attack)
            query = '''SELECT result, war_day_start, war_day_end FROM WARS WHERE war_id = ?'''
            cursor.execute(query, (war_id,))
            results = cursor.fetchall()
            if len(results) != 1:
                raise ValueError(
                    'Why do there seem to be war attacks for this war but the war is not saved? War id was: {}'.format(war_id))
            war_details_dict = {}
            war_details_dict['war_id'] = war_id
            war_details_dict['result'] = results[0][0]
            war_details_dict['war_day_start'] = results[0][1]
            war_details_dict['war_day_end'] = results[0][2]
            dict_for_this_war['war_details'] = war_details_dict
            result_dict['wars_participated_in'].append(dict_for_this_war)
            found += 1
        if found >= number_of_wars:
            break
    conn.close()
    return result_dict

def getIneligibleForClanGames(thLevelRequired=6):
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT member_name, town_hall_level FROM
			MEMBERS
		WHERE
			in_clan_currently = 1
		AND
			town_hall_level < ?
		'''
    cursor.execute(query, (thLevelRequired,))
    data = cursor.fetchall()
    resultsString = "These members are ineligible for clan games:\n"
    for entry in data:
        resultsString += entry[0] + ' (TH {})'.format(entry[1]) + '\n'
    conn.close()
    return resultsString


def getMembersWithScoreUnderThreshold(threshold, extraRequiredPerAccount=200):
    #	conn = sqlite3.connect(db_file)
    #	print(sqlite3.version)
    #	cursor = conn.cursor()
    cursor, conn = getCursorAndConnection()

    cursor.execute('SELECT MAX (clan_games_id) FROM CLAN_GAMES_SCORE')
    maxClanGamesID = cursor.fetchone()[0]
    data = []
#	ineligible = []
    for i in range(maxClanGamesID-4, maxClanGamesID+1):
        print('looping')

        cursor.execute(
            '''
			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
			FROM MEMBERS mems
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
			WHERE
				mems.town_hall_level >= (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_id = ?)
			AND
				CLAN_GAMES_SCORE.clan_games_id = ?
			AND
				mems.in_clan_currently = 1
			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_id;
			''', (i, i,)
        )
        results = cursor.fetchall()
        print(results)
        print(i)
        data.extend(results)
#		cursor.execute(
#			'''
#			SELECT mems.member_name, mems.member_tag, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
#			FROM MEMBERS mems
#			INNER JOIN CLAN_GAMES_SCORE
#				ON CLAN_GAMES_SCORE.member_tag = mems.member_tag
#			WHERE
#				mems.town_hall_level < (SELECT min_town_hall FROM CLAN_GAMES WHERE clan_games_id = ?)
#			AND
#				CLAN_GAMES_SCORE.clan_games_id = ?
#			AND
#				mems.in_clan_currently = 1
#			ORDER BY mems.member_name, CLAN_GAMES_SCORE.clan_games_id;
#			'''
#			,(i,i,)
#			)
#		ineligible.extend(cursor.fetchall())

    combinedScores = {}
    membersThatAreTooLow = []

    for entry in data:
        clanGamesID = entry[2]
        name = entry[0]
        tag = entry[1]
        score = entry[3]
        query = '''
			SELECT discord_tag FROM DISCORD_CLASH_LINKS
			WHERE 
				member_tag = ?
			'''
        cursor.execute(query, (tag,))
        discordTag = cursor.fetchone()
        if discordTag == None:
            print('{} has no discord'.format(name))
            if score <= threshold:
                membersThatAreTooLow.append((name, clanGamesID, score))
        else:
            print('{} has a discord'.format(name))
            discordTag = discordTag[0]
            query = '''
				
				'''

            if not discordTag in combinedScores:
                combinedScores[discordTag] = {}
                combinedScores[discordTag]['name'] = set()
                combinedScores[discordTag]['GamesList'] = {}
            combinedScores[discordTag]['name'].add(name)
            if clanGamesID not in combinedScores[discordTag]['GamesList']:
                combinedScores[discordTag]['GamesList'][clanGamesID] = 0
            combinedScores[discordTag]['GamesList'][clanGamesID] += score

    print(combinedScores)

    for discordTag in combinedScores:
        gamesList = combinedScores[discordTag]['GamesList']
        for clanGameID in gamesList:
            if gamesList[clanGameID] <= threshold + extraRequiredPerAccount*(len(combinedScores[discordTag]['name'])-1):
                names = combinedScores[discordTag]['name']
                name = ""
                for nameInd in names:
                    name += nameInd + "/"
                name = name[:-1]
                membersThatAreTooLow.append(
                    ((name, clanGameID, gamesList[clanGameID])))
                print('{} was below threshold'.format(name))
            else:
                print(combinedScores[discordTag]['name'])
                print('was above threshold')

    result = ""
    prevID = None

    conn.close()

    membersThatAreTooLow = sorted(membersThatAreTooLow, key=lambda x: x[0])

    for entry in membersThatAreTooLow:
        print(entry)
        result += str(entry[1]) + ") " + entry[0] + ' ' + str(entry[2]) + "\n"
    print(result)
    return result

def getAllLinkedAccountsList():
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT MEMBERS.member_name, DISCORD_CLASH_LINKS.discord_tag
		FROM MEMBERS
		INNER JOIN 
		DISCORD_CLASH_LINKS ON
		DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    conn.close()
    accounts = {}
    for entry in data:
        name = entry[0]
        discordTag = entry[1]
        if not discordTag in accounts:
            accounts[discordTag] = []
        accounts[discordTag].append(name)
    resultString = ""
    for id in accounts:
        for name in accounts[id]:
            resultString += name + '\n'
        resultString += '\n'
    return resultString

def getRosterChanges():
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT ADD_TO_WAR.change_number, MEMBERS.member_name 
		FROM 
			MEMBERS
		INNER JOIN ADD_TO_WAR
			ON ADD_TO_WAR.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    addedToWar = cursor.fetchall()
    query = '''
		SELECT REMOVE_FROM_WAR.change_number, MEMBERS.member_name 
		FROM 
			MEMBERS
		INNER JOIN REMOVE_FROM_WAR
			ON REMOVE_FROM_WAR.member_tag = MEMBERS.member_tag
		'''
    cursor.execute(query)
    removedFromWar = cursor.fetchall()
    conn.commit()
    conn.close()

    addedString = "No members being added to war.\n"
    if len(addedToWar) > 0:
        addedString = "These members will be added to war.\n"
        for account in addedToWar:
            addedString += '{}) {}\n'.format(account[0], account[1])

    removedString = "No members being removed from war.\n"
    if len(removedFromWar) > 0:
        removedString = "These members will be removed from war.\n"
        for account in removedFromWar:
            removedString += '{}) {}\n'.format(account[0], account[1])

    return addedString + removedString


def undoWarChange(changeNumber):
    changed = 0
    cursor, conn = getCursorAndConnection()
    query = '''
		DELETE FROM add_to_war 
		WHERE
		change_number = ?
		'''
    cursor.execute(query, (changeNumber,))
    changed += cursor.rowcount
    query = '''
		DELETE FROM remove_from_war 
		WHERE
		change_number = ?
		'''
    cursor.execute(query, (changeNumber,))
    changed += cursor.rowcount
    conn.commit()
    conn.close()
    return changed


def getClanGamesResultsForMemberName(memberName):
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT discord_tag FROM discord_clash_links
		INNER JOIN MEMBERS
			ON MEMBERS.member_tag = discord_clash_links.member_tag 
		WHERE
			UPPER(MEMBERS.member_name) = UPPER(?)
		'''
    cursor.execute(query, (memberName,))
    discordID = cursor.fetchone()

    if discordID is None:
        query = '''
			SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
			FROM MEMBERS			
			INNER JOIN CLAN_GAMES_SCORE
				ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
			WHERE
				UPPER(MEMBERS.member_name) = UPPER(?)
			ORDER BY CLAN_GAMES_SCORE.clan_games_id, MEMBERS.member_name
			'''
        cursor.execute(query, (memberName,))
        results = cursor.fetchall()

        resultsString = "Unable to find this account\n"

        if len(results) > 0:
            resultsString = "Here are your results:\n"
            previousClanGames = None
            for result in results:
                cgNumber = result[1]
                name = result[0]
                score = result[2]
                if result[1] != previousClanGames:
                    previousClanGames = result[1]
                    resultsString += '\n**Clan games \#{}:\n**'.format(
                        cgNumber)
                resultsString += '{} scored: {}\n'.format(name, score)
        return resultsString
    else:
        conn.close()
        return getClanGamesResultsFor(discordID[0])


def getClanGamesResultsFor(discordID):
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		SELECT MEMBERS.member_name, CLAN_GAMES_SCORE.clan_games_id, CLAN_GAMES_SCORE.score
		FROM MEMBERS			
		INNER JOIN CLAN_GAMES_SCORE
			ON CLAN_GAMES_SCORE.member_tag = MEMBERS.member_tag
		INNER JOIN DISCORD_CLASH_LINKS
			ON DISCORD_CLASH_LINKS.member_tag = MEMBERS.member_tag
		WHERE
			DISCORD_CLASH_LINKS.discord_tag = ?
		ORDER BY CLAN_GAMES_SCORE.clan_games_id, DISCORD_CLASH_LINKS.account_order, MEMBERS.member_name
		''', (discordID,))
    results = cursor.fetchall()

    resultsString = "Here are your results:\n"

    if len(results) > 0:
        previousClanGames = None
        for result in results:
            cgNumber = result[1]
            name = result[0]
            score = result[2]
            if result[1] != previousClanGames:
                previousClanGames = result[1]
                resultsString += '\n**Clan games \#{}:\n**'.format(cgNumber)
            resultsString += '{} scored: {}\n'.format(name, score)

    return resultsString


def checkTroopDonator(discordID, valExpected):
    result = False
    cursor, conn = getCursorAndConnection()
    query = '''
		SELECT is_troop_donator
		FROM DISCORD_PROPERTIES
		WHERE discord_tag = ?
		'''
    cursor.execute(query, (discordID,))
    answer = cursor.fetchone()
    if answer != None:
        answer = answer[0]
        if answer == valExpected:
            result = True
    return result


def setTroopDonator(discordID, val):
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		UPDATE DISCORD_PROPERTIES
		SET is_troop_donator = ?
		WHERE discord_tag = ?
		''',
        (val, discordID)
    )

    result = cursor.rowcount
    conn.commit()
    conn.close()
    return result

def getMembersInWarWithoutDiscordAsString():
    resultList = getMembersInWarWithoutDiscord()
    resultString = ""
    for entry in resultList:
        resultString += entry + '\n'
    return resultString


def getMembersInWarWithoutDiscord():
    cursor, conn = getCursorAndConnection()
    cursor.execute(
        '''
		SELECT MEMBERS.member_name
		FROM MEMBERS
		WHERE 
			MEMBERS.in_war_currently = 1

		AND MEMBERS.member_name NOT IN
			(
				SELECT MEMBERS.member_name
				FROM MEMBERS
				INNER JOIN DISCORD_CLASH_LINKS
					ON MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
				WHERE
					MEMBERS.in_war_currently = 1
			)
		'''
    )
    results = cursor.fetchall()
    conn.close()
    actualResults = []

    for result in results:
        actualResults.append(result[0])

    return actualResults


def getDiscordIDForAccountName(accountName):
    cursor, conn = getCursorAndConnection()
    query = '''SELECT DISCORD_CLASH_LINKS.discord_tag
		FROM DISCORD_CLASH_LINKS
		INNER JOIN MEMBERS
		ON MEMBERS.member_tag = DISCORD_CLASH_LINKS.member_tag
		WHERE UPPER(member_name) = ?
		'''
    cursor.execute(query, (accountName, ))
    results = cursor.fetchall()
    conn.close()
    return results


def setWarPermissionVal(memberName, val):
    discordID = 'somebs'
    discordIDRaw = getDiscordIDForAccountName(memberName)
    if len(discordIDRaw) > 0:
        discordID = discordIDRaw[0][0]
    cursor, conn = getCursorAndConnection()
    query = '''UPDATE DISCORD_PROPERTIES 
			SET has_permission_to_set_war_status = ? 
			WHERE discord_tag = ?
		'''

    cursor.execute(query, (val, discordID))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    return rowcount


def verifyAccountExists(memberName):
    memberName = memberName.upper()
    cursor, conn = getCursorAndConnection()
    query = '''SELECT * FROM MEMBERS WHERE UPPER(member_name) = ?'''
    cursor.execute(query, (memberName,))
    results = cursor.fetchall()
    conn.close()
    return len(results)


def getMembersWithPoorWarPerformance():
    cursor, conn = getCursorAndConnection()
    query = '''
            SELECT 
                member_tag, member_name 
            FROM
                members
            WHERE
                in_clan_currently = 1
            '''
    cursor.execute(query)
    results = cursor.fetchall()
    if len(results) == 0:
        return None

    num_wars_to_go_back = 5

    war_size_query = 'SELECT war_id, war_size FROM wars'
    cursor.execute(war_size_query)
    war_size_results = cursor.fetchall()
    war_size_dict = {war_id:war_size for (war_id, war_size) in war_size_results}

    # this is hacky but as I am in the middle of a rewrite this branch shouldn't
    # be used too long so ignore the ugly :)
    for entry in results:
        tag, name = entry
        member_tags = {tag:name}
        results = get_past_war_performance_for_member_tags(member_tags, num_wars_to_go_back)
        member_attacks_count = 0
        attack_deviations = []
        missed = 0
        zero_star = 0
        one_star = 0
        two_star = 0
        three_star = 0
        member_attacks_count_made = 0
        for entry in results['wars_participated_in']:
            #member_attacks.extend(entry['war_attacks'])
            this_war_id = entry['war_details']['war_id']
            this_war_size = war_size_dict[this_war_id]
            for attack in entry['war_attacks']:
                member_attacks_count += 1
                if attack['defender_town_hall'] == None:
                    missed += 1
                    continue
                elif attack['stars'] == 0:
                    zero_star += 1
                elif attack['stars'] == 1:
                    one_star += 1
                elif attack['stars'] == 2:
                    two_star += 1
                elif attack['stars'] == 3:
                    three_star += 1
                member_attacks_count_made += 1
                attacker_position_on_map = attack['attacker_position']
                defender_position_on_map = attack['defender_position']
                deviation = 100 * (attacker_position_on_map - defender_position_on_map) / this_war_size
                deviation = '{:.2f}'.format(deviation)
                attack_deviations.append(deviation)
#                print('attacker pos: {}'.format(attacker_position_on_map))
#                print('defender pos: {}'.format(defender_position_on_map))
#                print('dev: {}'.format(deviation))
        total_attacks = member_attacks_count
        if total_attacks == 0:
            percent_zero_star = '-'
            percent_one_star = '-'
            percent_two_star = '-'
            percent_three_star = '-'
            percent_no_show = '-'
        elif member_attacks_count_made == 0:
            percent_zero_star = '-'
            percent_one_star = '-'
            percent_two_star = '-'
            percent_three_star = '-'
            percent_no_show = '100'
        else:
            percent_zero_star = '{:.2f}'.format(100 * zero_star / member_attacks_count_made)
            percent_one_star = '{:.2f}'.format(100 * one_star / member_attacks_count_made)
            percent_two_star = '{:.2f}'.format(100 * two_star / member_attacks_count_made)
            percent_three_star = '{:.2f}'.format(100 * three_star / member_attacks_count_made)
            percent_no_show = '{:.2f}'.format(100 * missed / total_attacks)
            
        th_query = 'SELECT town_hall_level FROM members WHERE member_tag = ?'
        cursor.execute(th_query, (tag,))
        current_th = cursor.fetchall()[0][0]

        print(name)
        print('Current town hall: {}'.format(current_th))
        print('Number of attacks possible: {}'.format(member_attacks_count))
        print('Percentage no show: {}%'.format(percent_no_show))
        print('Number of attacks made: {}'.format(member_attacks_count_made))
        print('Percentage 3*: {}%'.format(percent_three_star))
        print('Percentage 2*: {}%'.format(percent_two_star))
        print('Percentage 1*: {}%'.format(percent_one_star))
        print('Percentage 0*: {}%'.format(percent_zero_star))
        print('Attack deviations: {}%'.format(attack_deviations))
        #print(member_attacks)
        print('')
    conn.close()


def init():
    if __name__ == "__main__":
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            result = database_accessor.get_all_donated_or_received_in_time_frame(1548518784, 1548524700)
            print(json.dumps(result, indent=4))
            #	result = getMembersFromLastWar()
            #result = getMembersWithScoreUnderThreshold(300)
            #print(result)
            # getMembersWithPoorWarPerformance()
            # print("I'm running but have no tasks")
            pass

init()