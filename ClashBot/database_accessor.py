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

    def get_member_strengths(self, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        # sort by member name, alphabetically
        members_in_clan = self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag) \
            .all()

        scores = {}
        for member in members_in_clan:
            member_score = member.town_hall_level
            member_score += member.king_level
            member_score += member.queen_level
            member_score += member.warden_level
            if member_score not in scores:
                scores[member_score] = []
            scores[member_score].append(member)

        output = []

        counter = 1
        for score in sorted(scores, reverse=True):
            for member in scores[score]:
                output.append({
                    "rank:": counter,
                    "member_name": member.member_name,
                    "town_hall_level": member.town_hall_level,
                    "king_level": member.king_level,
                    "queen_level": member.queen_level,
                    "grand_warden_level": member.warden_level
                })
                counter += 1

        return output

    def get_war_performance(self, num_wars_to_include=5, clan_tag=None):

        if clan_tag is None:
            clan_tag = self.my_clan_tag

        output = []

        members_in_clan = self.session.query(MEMBER) \
            .filter(MEMBER.clan_tag == clan_tag) \
            .all()

        for member in members_in_clan:

            member_attacks_count = 0
            attack_deviations = []
            missed = 0
            zero_star = 0
            one_star = 0
            two_star = 0
            three_star = 0
            member_attacks_count_made = 0

            for war_particip_key in list(member.war_participations.keys())[-num_wars_to_include:]:
                war_particip = member.war_participations[war_particip_key]

                war = war_particip.war
                if war.result == "in progress":
                    continue
                this_war_size = war.war_size

                if war_particip.is_clan_war_league_war:
                    attacks_to_process = [war_particip.attack1]
                else:
                    attacks_to_process = [war_particip.attack1, war_particip.attack2]
                for attack in attacks_to_process:
                    member_attacks_count += 1
                    if attack.defender_town_hall is None:
                        missed += 1
                        continue
                    elif attack.stars == 0:
                        zero_star += 1
                    elif attack.stars == 1:
                        one_star += 1
                    elif attack.stars == 2:
                        two_star += 1
                    elif attack.stars == 3:
                        three_star += 1
                    member_attacks_count_made += 1
                    attacker_position_on_map = attack.attacker_position
                    defender_position_on_map = attack.defender_position
                    deviation = 100 * (attacker_position_on_map - defender_position_on_map) / this_war_size
                    deviation = '{:.2f}'.format(deviation)
                    attack_deviations.append(deviation)
            if member_attacks_count == 0:
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
                percent_no_show = '{:.2f}'.format(100 * missed / member_attacks_count)

            output.append({
                "member_name": member.member_name,
                "town_hall": member.town_hall_level,
                "attacks_possible": member_attacks_count,
                "attacks_made": member_attacks_count_made,
                "percent_no_show": percent_no_show,
                "percent_0_star": percent_zero_star,
                "percent_1_star": percent_one_star,
                "percent_2_star": percent_two_star,
                "percent_3_star": percent_three_star,
                "deviations": attack_deviations,

            })
        return output

def init():
    if __name__ == "__main__":
        pass

init()