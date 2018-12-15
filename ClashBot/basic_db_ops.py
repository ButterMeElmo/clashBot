#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import dateutil.parser as dp
import json
import random
import unittest
import pytz
import datetime
import dateutil
import os
import math

from ClashBot import DateFetcherFormatter, SupercellDataFetcher
from ClashBot.models import ACCOUNTNAME, CLAN, MEMBER, SCANNEDDATA, WAR, WARATTACK, CLANGAME, SEASON, CALCULATEDTROOPSSPELLSSIEGE, SEASONHISTORICALDATA, CLANGAMESSCORE, WARPARTICIPATION, DISCORDACCOUNT, DISCORDCLASHLINK, LASTPROCESSED

from ClashBot import DatabaseSetup

from sqlalchemy.sql.expression import func

def TEMPORARY_FIX_determine_war_key(prep_day_start, enemy_tag, friendly_tag):
    return str(prep_day_start) + "-" + enemy_tag + "-" + friendly_tag

def TEMPORARY_FIX_determine_war_attack_key(war_id, attacker_tag, attacker_attack_number):
    return str(war_id) + "-" + attacker_tag + "-" + str(attacker_attack_number)

class BasicDBOps:

    def __init__(self, session=DatabaseSetup.get_session()):
        self.session = session

        print('loading data')

        print('loading last proccessed time')
        save_instance = self.session.query(LASTPROCESSED).filter(LASTPROCESSED.id == 1).first()
        if save_instance is None:
            # todo change this to an instance time instance?
            self.previous_processed_time_instance = LASTPROCESSED()
            self.previous_processed_time_instance.id = 1
            self.previous_processed_time_instance.time = 0
            self.session.add(self.previous_processed_time_instance)
        else:
            self.previous_processed_time_instance = save_instance

        # todo, pull this data from the DB

        # self.last_processed_achievements_and_games = 0
        self.previous_processed_sieges = 0

        print('loading clan games')
        clan_games = self.session.query(CLANGAME).all()
        self.clan_games = {}
        for clan_game in clan_games:
            self.clan_games[clan_game.start_time] = clan_game

        print('loading wars')
        self.wars = {}
        wars = self.session.query(WAR).all()
        for war in wars:
            key = TEMPORARY_FIX_determine_war_key(war.prep_day_start, war.enemy_tag, war.friendly_tag)
            self.wars[key] = war

        print('loading members')
        self.members = {}
        members = self.session.query(MEMBER).all()
        for member in members:
            self.members[member.member_tag] = member

        print('loading clans')
        self.clans = {}
        clans = self.session.query(CLAN).all()
        for clan in clans:
            self.clans[clan.clan_tag] = clan

        print('loading seasons')
        self.seasons = {}
        seasons = self.session.query(SEASON).all()
        for season in seasons:
            self.seasons[season.start_time] = season

        print('loaded data')

    def get_all_members_tag_supposedly_in_clan(self):

        # todo make this updated as I update members?
        results = [member for member in self.members.items() if member.clan_tag in self.clans]
        print('this is probably broken')
        print(results)
        return results

    # todo where should this live
    def convert_supercell_timestamp_string_to_epoch(self, time_as_string):
        # print("inputting as as string: {}".format(time_as_string))
        timestamp = dateutil.parser.parse(time_as_string).timestamp()
        # print('outputting {}'.format(timestamp))
        return int(timestamp)