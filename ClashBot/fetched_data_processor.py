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
from ClashBot.models import ACCOUNTNAME, CLAN, MEMBER, SCANNEDDATATIME, SCANNEDDATA

from ClashBot import DatabaseSetup

class BasicDBOps:
    def __init__(self, session):
        self.session = session
        self.previous_processed_time = 0
        self.last_processed_achievements_and_games = 0
        self.last_processed_sieges = 0

    def get_index_for_timestamp(self, timestamp):
        return self.session.query(SCANNEDDATATIME).filter_by(time=timestamp).first().scanned_data_index

class FetchedDataProcessor(BasicDBOps):

    def __init__(self, session, data_directory="data"):
        super().__init__(session)
        self.data_directory = data_directory

    date_fetcher_formatter = DateFetcherFormatter()

# importing data

    def use_linked_accounts_starting_point(self):
        pass

    def import_saved_free_gift_days(self):
        pass

# inserts
    def add_clan_to_db(self, clan_tag, clan_name):
        clan = self.session.query(CLAN).filter_by(clan_tag=clan_tag).first()
        if clan:
            clan.clan_name = clan_name
        else:
            clan_to_add = CLAN(clan_tag=clan_tag, clan_name=clan_name)
            self.session.add(clan_to_add)

    def add_member_to_db(self, data_time, **kwargs):

        if 'member_tag' not in kwargs:
            raise Exception('member_tag is required')

        member_tag = kwargs['member_tag']
        member_query = self.session.query(MEMBER).filter_by(member_tag=member_tag)
        print(member_query)
        member = member_query.first()
        print(member)
        if member:
            if data_time > member.last_updated_time:
                print('updating')
                member_query.update(kwargs)
        else:
            member_to_add = MEMBER(**kwargs)
            print('adding...')
            self.session.add(member_to_add)

    def add_scanned_data_to_db(self, **kwargs):

        if 'member_tag' not in kwargs:
            raise Exception('member_tag is required')

        if 'data_time' not in kwargs:
            raise Exception('data_time is required')

        scanned_data_time = kwargs['data_time']
        member_tag = kwargs['member_tag']

        self.add_scanned_data_time_to_db(scanned_data_time)
        scanned_data_index = self.session.query(SCANNEDDATATIME).filter_by(time=scanned_data_time).first().scanned_data_index

        scanned_data_instance_query = self.session.query(SCANNEDDATA).filter_by(scanned_data_index=scanned_data_index, member_tag=member_tag)
        scanned_data_instance = scanned_data_instance_query.first()
        if scanned_data_instance is None:
            kwargs.pop('data_time')
            kwargs['scanned_data_index'] = scanned_data_index
            scanned_data_instance_to_add = SCANNEDDATA(**kwargs)
            self.session.add(scanned_data_instance_to_add)

    def add_scanned_data_time_to_db(self, time_to_add):
        scanned_data_time = self.session.query(SCANNEDDATATIME).filter_by(time=time_to_add).first()
        if scanned_data_time is None:
            scanned_data_time_to_add = SCANNEDDATATIME(time=time_to_add)
            self.session.add(scanned_data_time_to_add)

    def add_account_name_to_db(self, tag, name):
        account_name = self.session.query(ACCOUNTNAME).filter_by(account_name=name, member_tag=tag).first()
        if account_name is None:
            account_name_to_add = ACCOUNTNAME(account_name=name, member_tag=tag)
            self.session.add(account_name_to_add)

    # reading data into database
    def save_data(self, previous_processed_time=0, ):
        # this contains all the info about the player
        self.process_player_achievement_files()

        # this contains details on the current war (at the time of saving)
        self.process_clan_war_details_files()

    def process_player_achievement_files(self):
        scdf = SupercellDataFetcher()
        for player_achievements_file in scdf.getFileNames(self.data_directory, 'clanPlayerAchievements', '.json', previous_processed_time):
            entries = json.load(open(player_achievements_file))
            for player_achievements_entry in entries:
                if self.previous_processed_time < player_achievements_entry['timestamp']:
                    self.process_player_achievements(player_achievements_entry)

    def process_clan_war_details_files(self):
        scdf = SupercellDataFetcher()
        for clan_war_details_file in scdf.getFileNames(self.data_directory, 'warDetailsLog', '.json', previous_processed_time):
            entries = json.load(open(clan_war_details_file))
            for clan_war_details_entry in entries:
                self.process_clan_war_details(clan_war_details_entry)

    def process_player_achievements(self, clan_player_achievements_entry):
        """
        This method takes in a list of members and their details at a particular timestamp.
        """
        # add the scanned data timestamp
        timestamp = clan_player_achievements_entry['timestamp']

        # todo, this should return the index
        self.add_scanned_data_time_to_db(timestamp)
        scanned_data_index = self.get_index_for_timestamp(timestamp)



        scanned_data_index = None
        
        # iterate through each player

        # update clan table

        # update members table
        
        # update account names table
        
        # add the scanned data to scanned data table

        pass

    def process_clan_war_details(self, session, war):
        pass
        def convertTime(timeStr):
            pass

    def processSeasonData(self, cursor, previousProcessedTime):
        pass
    def processClanGamesData(self, cursor, previousProcessedTime):
        pass
    def processClanProfile(self, clanProfile, cursor):
        pass

# having to manipulate data beyond simple converting from dict to class
    def getNextSeasonTimeStamp(self, timeBeingCalulatedFrom, extraMonth):
        pass
    def validateSeasons(self, cursor, previousProcessedTime):
        pass
    def populateSeasons(self, cursor, initialTime):
        pass
    def getMinAllowableTimeForClanGameData(self, clanGameData, currentGamesID):
        pass
    def getMaxAllowableTimeForClanGameData(self, clanGameData, currentGamesID):
        pass
    def attemptToFindSiegeMachinesSinceLastProcessed(self, cursor, previousProcessedTime):
        pass

# data from db I need to touch
    def findPositionAndTownHallForMemberTag(war, tag):
        pass
    def getSeasonIDForUTCTimestamp(cursor, timeToGetSeasonFor):
        pass
    def markProcessingTime(self, cursor, timestamp):
        pass
    #def getLastProcessedTime(self, cursor):

# these probably don't belong here
    def createEmptyWarAttack(self, warID, attackerTag, attackerPosition, attackerTownHall, attackNumber, dataTime):
        pass
    def markMembersNoLongerActive(self, cursor, profile):
        pass
    def DEBUG_ONLY_getMemberNameFromTag(self, cursor, tag):
        pass
    # importing old data

    

if __name__ == "__main__":
    db_path = "test.db"
    db_session = DatabaseSetup.get_session(engine_string="sqlite:////" + db_path)
    fdp = FetchedDataProcessor(db_session)
    fdp.save_data()
