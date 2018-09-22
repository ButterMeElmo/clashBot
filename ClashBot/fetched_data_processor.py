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
#from .supercell_data_fetcher import SupercellDataFetcher
import os
#from .database_accessor import DatabaseAccessor
import math

from ClashBot import DateFetcherFormatter
#from models import CLAN

from ClashBot import DatabaseSetup

class FetchedDataProcessor:
    

#    def save_data(self, session = DatabaseSetup.get_session(), previousProcessedTime = None):
#        clan_tag = "#hdgdurv2"
#        exists = session.query(CLAN).filter_by(clan_tag=clan_tag).first()
#        if exists:
#            print('exists')
#        else:
#            print('adding')
#            clan_1 = CLAN(clan_tag = clan_tag, clan_name = "clan name here!")
#            session.add(clan_1)
#            session.commit()
#        session.close()
    
    #currentSeasonIDs = {}

    date_fetcher_formatter = DateFetcherFormatter()

# imports
    def useOldClanGamesData(self, cursor):
        pass
    def useOldClanProfile(self, cursor):
        pass
    def useLinkedAccountsStartingPoint(self, cursor):
        pass
    def importSavedFreeGiftDays(self, cursor):
        pass

# inserts
    def addClanToDB(self, cursor, name, tag):
        pass
    def addMemberToDB(self, cursor, tag, name, role, townHallLevel, lastSeenInWar):
        pass
    def addDonationsToDB(self, cursor, clanTag, memberTag, donated, received, seasonID):
        pass
    def addWarAttackToDB(cursor, warAttackDict):
        pass
    def addWarToDB(self, cursor, friendlyTag, opponentTag, status, friendlyStars, opponentStars, friendlyDestructionPercentage, opponentDestructionPercentage, friendlyAttacks, opponentAttacks, warSize, prepStartTime, warStartTime, warEndTime):
        pass
    def addAccountName(self, cursor, playerTag, playerName):
        pass
    def addScannedDataToDB(self, cursor, data, scanned_data_index):
        pass
    def addMemberFromAchievements(self, entry, cursor, timestamp):
        pass
    def add_scanned_data_time(self, cursor, timestamp):
        pass
    def turnClanGamesStringIntoTimestamp(self, clangamesString):
        pass

# high level "processing"
    def processWar(self, war, cursor):
        pass
        def convertTime(timeStr):
            pass
    def processSeasonData(self, cursor, previousProcessedTime):
        pass
    def processClanGamesData(self, cursor, previousProcessedTime):
        pass
    def save_data(self, session = None, previousProcessedTime = None):       
        pass
    def processClanProfile(self, clanProfile, cursor):
        pass

# having to manipulate data beyond simple converting from dict to class
    def processClanPlayerAcievements(self, clanPlayerAcievementsEntry, cursor):
        pass
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
    fdp = FetchedDataProcessor()
    fdp.save_data()
