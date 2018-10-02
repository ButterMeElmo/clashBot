# -*- coding: utf-8 -*-

import discord
import asyncio
import getDataFromServer
import time
import datetime
import pytz
from discord.ext import commands
#import clashWebServer
import clashSaveData
import clashAccessData
import config_bot
import config_strings
import config_options
from MyHelpFormatter import MyHelpFormatter, _default_help_command
import clashConvertDataToString
import json

# make this come from config
botChannelID = config_bot.testingChannelID

#discordClient = discord.Client()
#discordClient = commands.Bot(command_prefix='!')

discordClient = commands.Bot(command_prefix='!', formatter=MyHelpFormatter())
discordClient.remove_command('help')
discordClient.command(**discordClient.help_attrs)(_default_help_command)

server = None

leader_nickname = config_bot.leader_nickname


@discordClient.event
async def on_member_join(member):
    """Says when a member joined."""
    msg = 'Hi {0.mention}! Please set up your account by typing: !start (including the exclamation point)'.format(
        member)
    generalChannel = discordClient.get_channel(config_bot.generalChannelID)
#	botChannel = discordClient.get_channel(config_bot.testingChannelID)
    await discordClient.send_message(generalChannel, msg)


@discordClient.event
async def on_member_remove(member):
    """Says when a member leaves/was kicked."""
    msg = '{0.mention} has left the server'.format(member)
#	generalChannel = discordClient.get_channel(config_bot.generalChannelID)
    botChannel = discordClient.get_channel(config_bot.testingChannelID)
    await discordClient.send_message(botChannel, msg)

# @commandBot.command(name='test')


@discordClient.command(pass_context=True, description='This is a sample description.', brief='Easy way to test notifications or if the bot is up', hidden=True)
async def test(ctx):
    discordID = ctx.message.author.id
    info = await discordClient.get_user_info(discordID)
    await discordClient.say('Hi ' + info.mention)


@discordClient.command(name='fetch', pass_context=True)
@commands.has_role("developers")
async def fetch(ctx):
    await discordClient.say('Working on it...')
    timeChecking = addTimeToCheck()
    while lastUpdatedData < timeChecking:
        await asyncio.sleep(1)


@discordClient.command(pass_context=True)
@commands.has_role("developers")
async def save(ctx):
    clashSaveData.saveData()
    await discordClient.say('Saved')


@discordClient.command(pass_context=True)
@commands.has_role("developers")
async def error(ctx):
    raise ValueError('Some error!')
    await discordClient.say('Threw error?')


class AccountManagement:

    @commands.command(name='removeaccountsrelatedto', pass_context=True,  brief='Set a reminder to collect your free gifts')
    @commands.has_role("developers")
    async def removeDiscordAccountsRelatedTo(self, ctx, *, accountName):
        accountName = accountName.upper()
        results = clashAccessData.removeDiscordAccountsRelatedTo(accountName)
        await discordClient.say('{} removed.'.format(results))

    @commands.command(name='setgiftreminder', pass_context=True,  brief='Set a reminder to collect your free gifts')
    @commands.has_role("developers")
    async def setGiftReminder(self, ctx):
        """Once a week, the trader brings a free potion for you. On that day, run this command, and then clashBot will remind you each week to collect the free potion!"""
        discordID = ctx.message.author.id
        dt = getDataFromServer.getUTCDateTime()
        dayOfWeek = dt.weekday()
        hour = dt.hour

        accounts = clashAccessData.getLinkedAccountsList(discordID)

        if len(accounts) == 0:
            await discordClient.say('you must link accounts first!')
        else:

            await discordClient.say('Which accounts got free gifts today?')
            for i in range(len(accounts)):
                account = accounts[i]
                message = await discordClient.say('{}) {}\n'.format(i+1, account))

                async def waitForResult(account, message, ctx):
                    await discordClient.add_reaction(message, config_strings.checkmark)
                    await discordClient.add_reaction(message, config_strings.xmark)

                    result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    if result.reaction.emoji == config_strings.checkmark:
                        resultStringTemp = clashAccessData.setMemberFreeGiftDayAndTime(
                            account, dayOfWeek, hour, discordID)
                        if resultStringTemp == config_strings.success:
                            resultString = 'Set gift reminder for {}.'.format(
                                account)
                        else:
                            resultString = 'Failed to set gift reminder for {}.'.format(
                                account)
                        await discordClient.send_message(ctx.message.channel, resultString)

                discordClient.loop.create_task(
                    waitForResult(account, message, ctx))

    @commands.command(name='start', pass_context=True,  brief='Connect your discord to a clash account')
    async def start(self, ctx):
        messageToSay = "Hi!\nI\'m clashBot and I am going to help you connect your Clash of Clans account to discord.\nSometimes, I\'ll ask you questions. Usually, you'll type a response, but sometimes I will let you hit a check ({}) for yes or an x ({}) for no. Sound good?".format(
            config_strings.checkmark, config_strings.xmark)
        message = await discordClient.say(messageToSay)
        await discordClient.add_reaction(message, config_strings.checkmark)
        await discordClient.add_reaction(message, config_strings.xmark)
        result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
        hitCheck = (result.reaction.emoji == config_strings.checkmark)
        if hitCheck:
            await discordClient.say('Great! Let\'s link your accounts now.')
            await account_management_cog.linkAccountsBeta.callback(self, ctx)
        else:
            await discordClient.say('Ok, well since you hit the x, please let {} know what your problem with this is.'.format(leader_nickname))

    @commands.command(name='linkmemberaccount', pass_context=True,  brief='Connect your discord to a clash account')
    @commands.has_role("developers")
    async def linkAccountsForMember(self, ctx):
        await discordClient.say('Whose account would you like to link?')
        message = await discordClient.wait_for_message(author=ctx.message.author)
        if len(message.mentions) > 0:
            discordID = message.mentions[0].id
            await account_management_cog.linkAccountsBeta.callback(self, ctx, discordID)
            await account_management_cog.checkLinkedAccounts.callback(self, ctx, discordID)
        else:
            await discordClient.say('Failed to find the mention')

    @commands.command(name='linkmyaccount', pass_context=True,  brief='Connect your discord to a clash account')
    async def linkAccountsBeta(self, ctx, discordID=None):
        """Link your Clash accounts to your discord account"""
        print('starting link')
        if discordID == None:
            discordID = ctx.message.author.id
        moreAccountsToAdd = True
        successfulAccounts = 0
        has_checked_if_should_refresh = False
        while moreAccountsToAdd == True:
            await discordClient.say(' \n\nPlease enter your clash account name:')
            message = await discordClient.wait_for_message(author=ctx.message.author)
            memberName = message.content.upper()
            result = clashAccessData.linkDiscordAccount(
                discordID, memberName, isName=True)
            await discordClient.say(result)
            if result == config_strings.successfully_linked_string:
                successfulAccounts += 1
                message = await discordClient.say("Do you have more clash accounts to add?\n")
                await discordClient.add_reaction(message, config_strings.checkmark)
                await discordClient.add_reaction(message, config_strings.xmark)
                result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                moreAccountsToAdd = (
                    result.reaction.emoji == config_strings.checkmark)
            elif result == config_strings.unable_to_find_account_string:
                hit_check = False
                if has_checked_if_should_refresh == False:
                    message = await discordClient.say("Was this account added to the clan in the last hour?")
                    await discordClient.add_reaction(message, config_strings.checkmark)
                    await discordClient.add_reaction(message, config_strings.xmark)
                    result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    hit_check = (result.reaction.emoji ==
                                 config_strings.checkmark)
                    has_checked_if_should_refresh = True
                if hit_check:
                    # force data update
                    await discordClient.say("Please wait while I refresh my data on the clan!")
                    timeChecking = addTimeToCheck()
                    while lastUpdatedData < timeChecking:
                        await asyncio.sleep(1)
                    await discordClient.say("Data has been refreshed. Enter the account name again in a moment when prompted.")
                else:
                    message = await discordClient.say("Do you want to try entering this account again? If you cannot find this account, please ask {}.".format(leader_nickname))
                    await discordClient.add_reaction(message, config_strings.checkmark)
                    await discordClient.add_reaction(message, config_strings.xmark)
                    result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    hit_check = (result.reaction.emoji ==
                                 config_strings.checkmark)
                    if not hit_check:
                        # no desire to continute

                        if successfulAccounts > 0:
                            moreAccountsToAdd = False
                        else:
                            await discordClient.say("Please let {} know that you were unable to resolve your issue.\n".format(leader_nickname))
                            return
            else:
                await discordClient.say("Please restart this command with !linkmyaccount\n")
                return

        # check if linked accounts contain one above TH 8
        allowedToDonate = clashAccessData.hasLinkedAccountWithTHLargerThan(
            discordID, config_options.minTHRequiredToBeADonator)

        if allowedToDonate:

            hasConfiguredIsTroopDonator = clashAccessData.hasConfiguredIsTroopDonator(
                discordID)

            if not hasConfiguredIsTroopDonator:
                message = await discordClient.say("Now that you have linked your account(s), would you like to become a troop donator? This means that during war, when people use the @troopdonator tag, you'll get a notification from discord, asking for troops.\n")
                await discordClient.add_reaction(message, config_strings.checkmark)
                await discordClient.add_reaction(message, config_strings.xmark)
                result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                if result.reaction.emoji == config_strings.checkmark:
                    resultString = self.processRoleRequest(discordID, 1)
                else:
                    resultString = self.processRoleRequest(discordID, 0)
                await discordClient.say(resultString)

        generalChannel = discordClient.get_channel(config_bot.generalChannelID)
        botChannel = discordClient.get_channel(config_bot.testingChannelID)
        try:
            await updateRoles()
            await discordClient.send_message(botChannel, "Applied roles")
        except:
            await discordClient.send_message(botChannel, "Failed to apply roles")

        # await updateRoles()

        introductionString = 'Your account(s) are all set up!\n'
        introductionString += 'During war, you may use @troopdonators to request troops for war.\n'
        rulesChannel = server.get_channel(config_bot.rulesChannelID)
        introductionString += 'Please see {} for the clan rules.\n'.format(
            rulesChannel.mention)
        warChannel = server.get_channel(config_bot.warChannelID)
        introductionString += 'Finally, we have a {} channel for discussing war.\n'.format(
            warChannel.mention)
        leader = server.get_member(config_bot.leaderDiscordID)
        introductionString += 'If you have any questions, please ask @{}!'.format(
            leader.nick)
        await discordClient.say(introductionString)

    @commands.command(name='linkmyaccountold', hidden=True, pass_context=True,  brief='Connect your discord to a clash account')
    async def linkAccounts(self, ctx, *, memberName):
        memberName = memberName.upper()
        discordID = ctx.message.author.id
        result = clashAccessData.linkDiscordAccount(
            discordID, memberName, isName=True)
        await discordClient.say(result)

    @commands.command(name='linkmyaccountbytag', pass_context=True, hidden=True)
    async def linkAccountsWithTag(self, ctx, member_tag):
        discordID = ctx.message.author.id
        result = clashAccessData.linkDiscordAccount(discordID, member_tag)
        await discordClient.say(result)

    @commands.command(name='checkmylinkedaccounts', pass_context=True,  brief='Check which clash accounts you have linked')
    async def checkLinkedAccounts(self, ctx, discordID=None):
        """Check which Clash accounts are linked with your discord."""
        if discordID == None:
            discordID = ctx.message.author.id
        results = clashAccessData.getLinkedAccounts(discordID)
        await discordClient.say(results)

    def processRoleRequest(self, discordID, val):
        result = clashAccessData.setTroopDonator(discordID, val)
        resultString = "You are now a troopdonator!"
        if val == 0:
            resultString = "You are now not a troopdonator."
        if result <= 0:
            resultString = "Unable to process request."

            # currently I don't ever hit this code block... do I want to?
            newResult = clashAccessData.checkTroopDonator(discordID, val)
            if newResult == True:
                if val == 1:
                    resultString = "You already had this role!"
                if val == 0:
                    resultString = "You didn't have this role anyways!"
        return resultString

    @commands.command(name='changemydonatorstatus', pass_context=True,  brief='Request to become or stop being a @troopdonator.')
    async def addDonatorRole(self, ctx):

        message = await discordClient.say('Would you like to be a troopdonator?')

        discordID = ctx.message.author.id

        await discordClient.add_reaction(message, config_strings.checkmark)
        await discordClient.add_reaction(message, config_strings.xmark)

        result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
        if result.reaction.emoji == config_strings.checkmark:
            wantToBeDonator = True
        else:
            wantToBeDonator = False
        resultString = self.processRoleRequest(discordID, wantToBeDonator)
        await discordClient.send_message(ctx.message.channel, resultString)

        botChannel = discordClient.get_channel(config_bot.testingChannelID)
        try:
            await updateRoles()
            await discordClient.send_message(botChannel, "Applied roles")
        except:
            await discordClient.send_message(botChannel, "Failed to apply roles")


#		await updateRoles()

class ClanWar:

    @commands.command(name='lastroster', pass_context=True,  brief='See the last war roster')
    @commands.has_role("developers")
    async def getClanWarRoster(self, ctx):
        await discordClient.say('Working on it...')
        timeChecking = addTimeToCheck()
        while lastUpdatedData < timeChecking:
            await asyncio.sleep(1)

        roster = clashAccessData.getMembersFromLastWar()
        await discordClient.say(roster)

    @commands.command(name='newroster', pass_context=True,  brief='See the new war roster with changes')
    @commands.has_role("coleaders")
    async def getNewClanWarRoster(self, ctx):
        """Generate a new war roster with all changes that were requested."""
        await discordClient.say('Working on it...')
        timeChecking = addTimeToCheck()
        while lastUpdatedData < timeChecking:
            await asyncio.sleep(1)

        roster = clashAccessData.getNewWarRoster()
        await discordClient.say(roster)

    @commands.command(name='newrosternopull', pass_context=True,  brief='See the new war roster with changes')
    @commands.has_role("coleaders")
    async def getNewClanWarRoster2(self, ctx):
        """Generate a new war roster with all changes that were requested."""
        await discordClient.say('Working on it...')
        roster = clashAccessData.getNewWarRoster()
        await discordClient.say(roster)

    @commands.command(name='clearrosterchanges', pass_context=True,  brief='Remove all war roster changes')
    @commands.has_role("developers")
    async def clearWarChanges(self, ctx):
        clashAccessData.clearAddAndRemoveFromWar()
        await discordClient.say('done')

    @commands.command(name='undorosterchange', pass_context=True,  brief='Remove a specific war roster change')
    @commands.has_role("developers")
    async def undoAWarChange(self, ctx):
        while True:
            changes = clashAccessData.getRosterChanges()
            await discordClient.say(changes)
            await discordClient.say('What change would you like to undo?')
            message = await discordClient.wait_for_message(author=ctx.message.author)
            changeNumber = int(message.content)
            result = clashAccessData.undoWarChange(int(changeNumber))
            await discordClient.say('{} changes made'.format(result))

            message = await discordClient.say('Would you like to undo another change?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discordClient.send_message(ctx.message.channel, resultString)

    @commands.command(name='seerosterchanges', pass_context=True,  brief='See all war roster changes for the next war')
    async def seeWarChanges(self, ctx):
        results = clashAccessData.getRosterChanges()
        await discordClient.say(results)

    @commands.command(name='removememberfromwar', pass_context=True,  brief='Remove someone else from war')
    @commands.has_role("developers")
    async def removeFromWar(self, ctx):
        while True:
            await discordClient.say('Who would you like to remove from war?')
            message = await discordClient.wait_for_message(author=ctx.message.author)

            clashAccountName = message.content.upper()
            result = clashAccessData.removeMemberFromWar(clashAccountName)
            await discordClient.say(result)

            message = await discordClient.say('Would you like to remove someone else from war?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discordClient.send_message(ctx.message.channel, resultString)

    @commands.command(name='addmembertowar', pass_context=True,  brief='Add someone else to war')
    @commands.has_role("developers")
    async def addToWar(self, ctx):
        while True:
            await discordClient.say('Who would you like to add to war?')
            message = await discordClient.wait_for_message(author=ctx.message.author)

            clashAccountName = message.content.upper()
            result = clashAccessData.addMemberToWar(clashAccountName)
            await discordClient.say(result)

            message = await discordClient.say('Would you like to add someone else to war?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break

    @commands.command(name='checkmypastwarperformance', pass_context=True,  brief="Check member's past war performance")
    @commands.has_role("developers")
    async def checkMyPastWarPerformance(self, ctx):
        discordID = ctx.message.author.id
        results_dict = clashAccessData.getPastWarPerformance(discordID, 5)
        results = clashConvertDataToString.convert_war_attacks_to_string(
            results_dict)
        try:
            await discordClient.say(results)
        except:
            await discordClient.say('error sending')

    @commands.command(name='checkmemberpastwarperformance', pass_context=True,  brief="Check member's past war performance")
    @commands.has_role("developers")
    async def checkMemberPastWarPerformance(self, ctx, number_of_wars=5):
        while True:
            await discordClient.say('Who would you like to see the past performance of?')
            message = await discordClient.wait_for_message(author=ctx.message.author)

            clashAccountName = message.content.upper()
            try:
                resultDict = clashAccessData.getPastWarPerformanceForMemberName(
                    clashAccountName, number_of_wars)
                resultString = clashConvertDataToString.convert_war_attacks_to_string(
                    resultDict)
            except ValueError as e:
                resultString = e
            try:
                await discordClient.say(resultString)
            except:
                await discordClient.say('error sending')

            message = await discordClient.say('Would you like to check someone else?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break

    @commands.command(name='changemywarstatus', pass_context=True,  brief='Change your war status')
    @commands.has_role("has_war_permissions")
    async def changeWarStatus(self, ctx):
        discordID = ctx.message.author.id

        # get accounts currently in clan
        accounts = clashAccessData.getLinkedAccountsList(
            discordID, currently_in_clan_required=True)

        if len(accounts) == 0:
            await discordClient.say('you must link accounts first!')
        else:
            question = 'Please hit the check on any accounts you want to add to war, and the x on any you want to remove from war.'
            await discordClient.say(question)
            for i in range(len(accounts)):
                account = accounts[i]

                message = await discordClient.say('{}) {}\n'.format(i+1, account))

                async def waitForResult(account, message, ctx):

                    await discordClient.add_reaction(message, config_strings.checkmark)
                    await discordClient.add_reaction(message, config_strings.xmark)

                    result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    if result.reaction.emoji == config_strings.checkmark:
                        resultStringTemp = clashAccessData.addMemberToWar(
                            account)
                        if resultStringTemp == config_strings.success:
                            resultString = '{} added to war'.format(account)
                        else:
                            resultString = 'Failed to add {} to war'.format(
                                account)
                    else:
                        resultStringTemp = clashAccessData.removeMemberFromWar(
                            account)
                        if resultStringTemp == config_strings.success:
                            resultString = '{} removed from war'.format(
                                account)
                        else:
                            resultString = 'Failed to remove {} from war'.format(
                                account)
                    await discordClient.send_message(ctx.message.channel, resultString)

                discordClient.loop.create_task(
                    waitForResult(account, message, ctx))


class ClanGames:
    @commands.command(name='checkmyCGscores', pass_context=True,  brief='Check your recent Clan Games scores')
    async def checkMyCGScores(self, ctx):
        discordID = ctx.message.author.id
        results = clashAccessData.getClanGamesResultsFor(discordID)
        await discordClient.say(results)

    @commands.command(name='checkmemberCGscores', pass_context=True,  brief='Check other members Clan Games scores')
    @commands.has_role("developers")
    async def checkMembersCGScores(self, ctx):

        while True:
            await discordClient.say('Who would you like to get Clan Games scores for?')
            message = await discordClient.wait_for_message(author=ctx.message.author)
            memberName = message.content.upper()
            results = clashAccessData.getClanGamesResultsForMemberName(
                memberName)
            await discordClient.say(results)

            message = await discordClient.say('Would you like to check another account?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discordClient.send_message(ctx.message.channel, resultString)

    @commands.command(name='checklowCGscores', pass_context=True,  brief='Get members underperforming in the clan games.')
    @commands.has_role("developers")
    async def getClanGamesScores(self, ctx, threshold=250):
        await discordClient.say('Working on it...')
        roster = clashAccessData.getMembersWithScoreUnderThreshold(threshold)
        await discordClient.say(roster)

    @commands.command(name='checkineligibleforCG', pass_context=True,  brief='Get members that are too low TH for the CGs.')
    @commands.has_role("developers")
    async def getIneligibleTHs(self, ctx):
        roster = clashAccessData.getIneligibleForClanGames()
        await discordClient.say(roster)


class ClanManagement:
    @commands.command(name='trackdonations', pass_context=True)
    @commands.has_role("developers")
    async def trackBadDonations(self, ctx):
        discordID = ctx.message.author.id
        await discordClient.say('How long ago was the request made, in minutes? (Over estimate if needed)')
        message = await discordClient.wait_for_message(author=ctx.message.author)
        currentTimestamp = getDataFromServer.getUTCTimestamp()
        timeSinceCreated = currentTimestamp - int(message.content) * 60
        await discordClient.say('How long ago was the request filled, in minutes? (Under estimate if needed, 0 if necessary)')
        message = await discordClient.wait_for_message(author=ctx.message.author)
        timeSinceFilled = currentTimestamp - int(message.content) * 60

        if timeSinceFilled > lastUpdatedData:
            timeChecking = addTimeToCheck()
            while lastUpdatedData < timeChecking:
                await asyncio.sleep(1)

        resultDict = clashAccessData.getAllDonatedOrReceivedInTimeFrame(
            timeSinceCreated, timeSinceFilled)
        resultString = clashConvertDataToString.convert_donation_timeframe_results(
            resultDict)
        await discordClient.say(str(resultDict))
        await discordClient.say(resultString)

    @commands.command(name='getallmemberswithoutdiscord', pass_context=True)
    @commands.has_role("developers")
    async def getAllMembersWithoutDiscord(self, ctx):
        discordID = ctx.message.author.id
        results = clashAccessData.getAllMembersWithoutDiscordAsString()
        await discordClient.say(results)

    @commands.command(name='getwarmemberswithoutdiscord', pass_context=True)
    @commands.has_role("developers")
    async def getWarMembersWithoutDiscord(self, ctx):
        discordID = ctx.message.author.id
        results = clashAccessData.getMembersInWarWithoutDiscordAsString()
        await discordClient.say(results)

    @commands.command(name='linkothersaccount', pass_context=True)
    @commands.has_role("developers")
    async def linkOthersAccounts(self, ctx, discordID, memberName):
        """Allows developer to provide a discord id and membername to link an account, should use linkmemberaccount instead"""
        memberName = memberName.upper()
        result = clashAccessData.linkDiscordAccount(
            discordID, memberName, isName=True)
        await discordClient.say(result)

    @commands.command(name='seealllinkedaccounts', pass_context=True)
    @commands.has_role("developers")
    async def seeAllLinkedAccounts(self, ctx):
        result = clashAccessData.getAllLinkedAccountsList()
        await discordClient.say(result)

    @commands.command(name='remindtostart', pass_context=True)
    @commands.has_role("developers")
    async def remindToStart(self, ctx):
        await discordClient.say('Who would you like to remind to setup their account?')
        message = await discordClient.wait_for_message(author=ctx.message.author)
        if len(message.mentions) > 0:
            discordID = message.mentions[0]
            await discordClient.on_member_join(discordID)
        else:
            await discordClient.say('Failed to find the mention')

    @commands.command(name='givememberwarpermissions', pass_context=True)
    @commands.has_role("developers")
    async def giveMemberWarPermissions(self, ctx):
        discordID = ctx.message.author.id
        await discordClient.say('Who would you like to set war permissions for?')
        message = await discordClient.wait_for_message(author=ctx.message.author)
        memberName = message.content.upper()
        accountExists = clashAccessData.verifyAccountExists(memberName)
        if accountExists:
            message = await discordClient.say('Should this account have permissions?')
            await discordClient.add_reaction(message, config_strings.checkmark)
            await discordClient.add_reaction(message, config_strings.xmark)

            result = await discordClient.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                count = clashAccessData.setWarPermissionVal(memberName, 1)
            else:
                count = clashAccessData.setWarPermissionVal(memberName, 0)
            await discordClient.say('{} rows changed.'.format(count))
            try:
                await updateRoles()
                await discordClient.say("Applied roles")
            except:
                await discordClient.say("Failed to apply roles")
        else:
            await discordClient.say('Unable to find this account')


clan_war_clog = ClanWar()
discordClient.add_cog(clan_war_clog)

clan_management_cog = ClanManagement()
discordClient.add_cog(clan_management_cog)

clan_games_cog = ClanGames()
discordClient.add_cog(clan_games_cog)

account_management_cog = AccountManagement()
discordClient.add_cog(account_management_cog)


async def updateRoles():

    print('updating roles')
    roles = server.roles

    def find(f, seq):
        """Return first item in sequence where f(item) == True."""
        for item in seq:
            if f(item):
                return item
        return None
    memberRole = find(lambda role: role.name == 'members', roles)
    warRole = find(lambda role: role.name == 'war', roles)
    troopRole = find(lambda role: role.name == 'troopdonators', roles)
    checkInRole = find(lambda role: role.name == 'MIAUsers', roles)
    warPermsRole = find(lambda role: role.name == 'has_war_permissions', roles)
    th12Role = find(lambda role: role.name == 'TH12', roles)

    discordIDsOfMembersInClan = clashAccessData.getMembersInClan()
    discordIDsOfWarParticipants = clashAccessData.getDiscordMembersInWar()
    discordIDsOfMembersWithWarPermissions = clashAccessData.getDiscordIDsOfMembersWithWarPermissions()
    discordIDsOfMembersWhoAreTH12 = clashAccessData.getDiscordIDsOfMembersWhoAreTH12()

    # go through everyone in discord
    for serverMember in server.members:

        if serverMember.bot:
            continue
        serverMemberID = serverMember.id

        if serverMemberID in discordIDsOfMembersInClan:
            rolesToAdd = []
            rolesToRemove = []

            if not memberRole in serverMember.roles:
                rolesToAdd.append(memberRole)

            isTroopDonator = discordIDsOfMembersInClan[serverMemberID]
            if isTroopDonator == 1:
                if not troopRole in serverMember.roles:
                    rolesToAdd.append(troopRole)
            else:
                if troopRole in serverMember.roles:
                    rolesToRemove.append(troopRole)

            if serverMemberID in discordIDsOfMembersWithWarPermissions:
                if not warPermsRole in serverMember.roles:
                    rolesToAdd.append(warPermsRole)
            else:
                if warPermsRole in serverMember.roles:
                    rolesToRemove.append(warPermsRole)

            if serverMemberID in discordIDsOfWarParticipants:
                if not warRole in serverMember.roles:
                    rolesToAdd.append(warRole)
            else:
                if warRole in serverMember.roles:
                    rolesToRemove.append(warRole)

            if serverMemberID in discordIDsOfMembersWhoAreTH12:
                if not th12Role in serverMember.roles:
                    rolesToAdd.append(th12Role)
            else:
                if th12Role in serverMember.roles:
                    rolesToRemove.append(th12Role)

            # update roles
            if len(rolesToAdd) > 0:
                await discordClient.add_roles(serverMember, *rolesToAdd)
            if len(rolesToRemove) > 0:
                for role in rolesToRemove:
                    print(role)
                await discordClient.remove_roles(serverMember, *rolesToRemove)
        # if not in clan, remove roles
        else:
            if len(serverMember.roles) > 1:
                await discordClient.remove_roles(serverMember, memberRole, warRole, troopRole, checkInRole)

    print('done updating!')


def updateTimesToCheckData():

    currentDateTime = getDataFromServer.getUTCDateTime()
    print('current:           {}'.format(currentDateTime.timestamp()))

    currentRoundedDownToHourAnd5 = datetime.datetime(
        currentDateTime.year, currentDateTime.month, currentDateTime.day, currentDateTime.hour, 5).replace(tzinfo=pytz.utc)
    print('currentRoundedDown {}'.format(
        currentRoundedDownToHourAnd5.timestamp()))

    if currentDateTime < currentRoundedDownToHourAnd5:
        nextTimeToCheckData = currentRoundedDownToHourAnd5.timestamp()
    else:
        nextHourAnd5 = currentRoundedDownToHourAnd5.timestamp() + (60 * 60)
        print('5pastnexthour      {}'.format(nextHourAnd5))
        nextTimeToCheckData = nextHourAnd5
    print('nextTime:          {}'.format(nextTimeToCheckData))

#	currentDateTime = datetime.datetime.utcnow()
#	currentRoundedDownToHour = datetime.datetime(currentDateTime.year, currentDateTime.month, currentDateTime.day, currentDateTime.hour)
#	currentRoundedDownToHourSeconds = currentRoundedDownToHour.replace(tzinfo=pytz.utc).timestamp() + 300
#	nextRoundedDownToHourSeconds = currentRoundedDownToHourSeconds + (60 * 60)
#	if currentRoundedDownToHourSeconds not in timesToCheckData and lastFetchedData < currentRoundedDownToHourSeconds:
#		timesToCheckData.append(currentRoundedDownToHourSeconds)
#	if nextRoundedDownToHourSeconds not in timesToCheckData and lastFetchedData < nextRoundedDownToHourSeconds:
#		timesToCheckData.append(nextRoundedDownToHourSeconds)
#
#	timesToCheckData.sort()
#
# print("current:")
#	currentTimeEpoch = currentDateTime.replace(tzinfo=pytz.utc).timestamp()
# print(currentTimeEpoch)
# print("list:")
# for entry in timesToCheckData:
# print(entry)
#
    return nextTimeToCheckData


timesToCheckData = []

dataCheckOverride = False

# todo change this...
lastUpdatedData = 0


def addTimeToCheck():
    #	if timestampTest == None:
    timestampTest = getDataFromServer.getUTCTimestamp()
#	global timesToCheckData
#	timesToCheckData.append(timestampTest)
    global dataCheckOverride
    dataCheckOverride = True

    return timestampTest


async def sendOutGiftReminders():

    botChannel = discordClient.get_channel(botChannelID)
    generalChannel = discordClient.get_channel(config_bot.generalChannelID)

    while True:
        currentDateTime = getDataFromServer.getUTCDateTime()
        currentDateTimeTimestamp = int(currentDateTime.timestamp())
        accountsWithGiftsOnIt = clashAccessData.getAccountsWhoGetGiftReminders(
            currentDateTime)
        for entry in accountsWithGiftsOnIt:
            discordID = str(entry['discord'])
            accountName = entry['accountName']
            member = server.get_member(discordID)
            await discordClient.send_message(botChannel, 'Hey {}, {} gets a free gift today!'.format(member.mention, accountName))
            await asyncio.sleep(1)
        nextTimestamp = currentDateTimeTimestamp + 3600
        timeToSleep = nextTimestamp - currentDateTimeTimestamp
        await asyncio.sleep(timeToSleep)


async def sendOutWarReminders():
    warChannel = discordClient.get_channel(config_bot.warChannelID)
    botChannel = discordClient.get_channel(config_bot.testingChannelID)
    while True:
        nextTimestampsForWar = clashAccessData.getTimestampsForCurrentWar()
        if nextTimestampsForWar == None:
            await asyncio.sleep(3600*6)
        else:
            nextWarTimestamp = nextTimestampsForWar[0][0]
            nextWarTimestampString = nextTimestampsForWar[0][1]
            timeToSleep = nextWarTimestamp - getDataFromServer.getUTCTimestamp()
            await asyncio.sleep(timeToSleep)

            # update data to be sure we aren't sending reminders to people who have already attacked, just recently
            timeChecking = addTimeToCheck()
            while lastUpdatedData < timeChecking:
                await asyncio.sleep(1)

            accountsThatNeedToAttack = clashAccessData.getMembersInWarWithAttacksRemaining()
            for discordID in accountsThatNeedToAttack:
                accountNamesDict = accountsThatNeedToAttack[discordID]
                accountNamesString = ""
                accountsTotal = len(accountNamesDict)
                currentAccount = 0
                for accountName in accountNamesDict:
                    numberOfAttacks = accountNamesDict[accountName]
                    if numberOfAttacks == 1:
                        accountNamesString += ' your {} attack with {}'.format(
                            numberOfAttacks, accountName)
                    else:
                        accountNamesString += ' your {} attacks with {}'.format(
                            numberOfAttacks, accountName)
                    if currentAccount == accountsTotal - 1:
                        # last account, do nothing at the end
                        accountNamesString += ''
                    elif currentAccount == accountsTotal - 2 and accountsTotal == 2:
                        accountNamesString += ' and'
                    elif currentAccount == accountsTotal - 2:
                        accountNamesString += ', and'
                    else:
                        accountNamesString += ','
                    currentAccount += 1
                discordID = str(discordID)
                member = server.get_member(discordID)
                await discordClient.send_message(warChannel, 'Hey {}, make sure to use{}! {}'.format(member.mention, accountNamesString, nextWarTimestampString))
                await asyncio.sleep(1)


async def createRules():
    rulesChannel = discordClient.get_channel(config_bot.rulesChannelID)
    async for x in discordClient.logs_from(rulesChannel, limit=9):
        await discordClient.delete_message(x)
    with open('clanRules.json') as rulesFiles:
        newRules = json.load(rulesFiles)
        for x in newRules["Rules"]:
            x['type'] = 'rich'
            newEmbed = discord.Embed(**x)
            await discordClient.send_message(rulesChannel, embed=newEmbed)


async def startGatheringData():

    print('startGatheringData starting')

    global timesToCheckData
    global lastUpdatedData
    global dataCheckOverride

    lastUpdatedData = clashAccessData.getLastProcessedTime()

    # this is last retrieved, regardless of failure
    lastFetched = clashAccessData.getLastProcessedTime()

    # this handles startups, but prevents spammy startups when restarting several times in a row
    if getDataFromServer.getUTCTimestamp() - lastFetched > 60 * 60:
        dataCheckOverride = True

    await discordClient.wait_until_ready()
    botChannel = discordClient.get_channel(botChannelID)

    global server
    server = discordClient.get_server(config_bot.generalChannelID)

    discordClient.loop.create_task(sendOutGiftReminders())
    discordClient.loop.create_task(sendOutWarReminders())
    # discordClient.loop.create_task(createRules())

    await discordClient.send_message(botChannel, "Coming online")

    nextTimeToCheckData = updateTimesToCheckData()
    try:
        while True:
            currentTimeSeconds = int(time.time())
#			print("\n\nUpdating")

            # allows discord to request a check whenever
            # check once an hour normally
            # prevent checks more than every 10 minutes in case of restarts, unless its been overridden
#			if dataCheckOverride == False and (currentTimeSeconds < timesToCheckData[0] or currentTimeSeconds < clashAccessData.getLastProcessedTime()+3000):
#				#print("current in loop:")
#				print(currentTimeSeconds)
#				#print(timesToCheckData[0])
#				#print("sleeping")
#				await asyncio.sleep(1)
#				continue

#			print("\n")
#			print('cur: {}'.format(currentTimeSeconds))
#			print('nex: {}'.format(nextTimeToCheckData))

            if dataCheckOverride == True:
                pass
            elif currentTimeSeconds >= nextTimeToCheckData:
                nextTimeToCheckData = updateTimesToCheckData()
#			elif currentTimeSeconds >= timesToCheckData[0] and currentTimeSeconds >= clashAccessData.getLastProcessedTime()+3000:
#				print('is this really what I want?')
                pass
            else:
                #print("current in loop:")
                # print(currentTimeSeconds)
                # print(timesToCheckData[0])
                # print("sleeping")
                await asyncio.sleep(1)
                continue

            lastFetched = getDataFromServer.getUTCTimestamp()
            dataCheckOverride = False

            print("getting data")

            try:
                await discordClient.send_message(botChannel, "Getting data")
                getDataFromServer.getDataFromServer()
                await asyncio.sleep(1)
                try:
                    dataValid = getDataFromServer.validateData()
                except IOError as e:
                    await discordClient.send_message(botChannel, "The data file doesn't exist to validate {}".format(e))
                    dataValid = False
            except Exception as e:
                print(e)
                await discordClient.send_message(botChannel, "error, trying again momentairily")
                await asyncio.sleep(60)
                getDataFromServer.getDataFromServer()
                dataValid = getDataFromServer.validateData()
            if dataValid:
                await discordClient.send_message(botChannel, "Data was retreived")
                try:
                    clashSaveData.saveData()
                    await asyncio.sleep(1)
                    lastUpdatedData = getDataFromServer.getUTCTimestamp()
                    await discordClient.send_message(botChannel, "Data was saved")
                    try:
                        await updateRoles()
                        await discordClient.send_message(botChannel, "Applied roles")
                    except:
                        await discordClient.send_message(botChannel, "Failed to apply roles")
                except:
                    await discordClient.send_message(botChannel, "Data failed to save")
            else:
                await discordClient.send_message(botChannel, "Data was not retreived")

    except Exception as err:
        print("Error: " + str(err))

discordClient.loop.create_task(startGatheringData())

discordToken = config_bot.token
discordClient.run(discordToken)
