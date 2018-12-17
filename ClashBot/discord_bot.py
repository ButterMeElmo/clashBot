# -*- coding: utf-8 -*-

import discord
import asyncio
import time
import datetime
import pytz
from discord.ext import commands
#import clashWebServer
from ClashBot import FetchedDataProcessor, DatabaseAccessor, DateFetcherFormatter, MyConfigBot, SupercellDataFetcher, DatabaseSetup
from my_help_formatter import MyHelpFormatter, _default_help_command
# import clashAccessData
# import MyConfigBot
import config_strings
import config_options
# from MyHelpFormatter import , _default_help_command
import clash_convert_data_to_string
import json

# make this come from config
botChannelID = MyConfigBot.testingChannelID

discord_client = commands.Bot(command_prefix='!', formatter=MyHelpFormatter())
discord_client.remove_command('help')
discord_client.command(**discord_client.help_attrs)(_default_help_command)

server = None

leader_nickname = MyConfigBot.leader_nickname

data_fetcher = SupercellDataFetcher()
fetched_data_processor = FetchedDataProcessor(data_directory=MyConfigBot.testing_data_dir)
database_accessor = DatabaseAccessor()

@discord_client.event
async def on_member_join(member):
    """Says when a member joined."""
    msg = 'Hi {0.mention}! Please set up your account by typing: !start (including the exclamation point)'.format(
        member)
    general_channel = discord_client.get_channel(MyConfigBot.generalChannelID)
    # botChannel = discord_client.get_channel(MyConfigBot.testingChannelID)
    await discord_client.send_message(general_channel, msg)


@discord_client.event
async def on_member_remove(member):
    """Says when a member leaves/was kicked."""
    msg = '{0.mention} has left the server'.format(member)
    # generalChannel = discord_client.get_channel(MyConfigBot.generalChannelID)
    bot_channel = discord_client.get_channel(MyConfigBot.testingChannelID)
    await discord_client.send_message(bot_channel, msg)

# @commandBot.command(name='test')


@discord_client.command(pass_context=True, description='This is a sample description.', brief='Easy way to test notifications or if the bot is up', hidden=True)
async def test(ctx):
    discord_id = ctx.message.author.id
    info = await discord_client.get_user_info(discord_id)
    await discord_client.say('Hi ' + info.mention)


@discord_client.command(name='fetch', pass_context=True)
@commands.has_role("developers")
async def fetch(ctx):
    await discord_client.say('Working on it...')
    time_checking = add_time_to_check()
    while fetched_data_processor.previous_processed_time_instance.time < time_checking:
        await asyncio.sleep(1)


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def save(ctx):
    fetched_data_processor.save_data()
    await discord_client.say('Saved')


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def error(ctx):
    raise ValueError('Some error!')
    await discord_client.say('Threw error?')


class AccountManagement:

    @commands.command(name='removeaccountsrelatedto', pass_context=True,  brief='Set a reminder to collect your free gifts')
    @commands.has_role("developers")
    async def remove_discord_accounts_related_to(self, ctx, *, account_name):
        account_name = account_name.upper()
        results = clashAccessData.remove_discord_accounts_related_to(account_name)
        await discord_client.say('{} removed.'.format(results))

    @commands.command(name='setgiftreminder', pass_context=True,  brief='Set a reminder to collect your free gifts')
    @commands.has_role("developers")
    async def set_gift_reminder(self, ctx):
        """Once a week, the trader brings a free potion for you. On that day, run this command, and then clashBot will remind you each week to collect the free potion!"""
        discord_id = ctx.message.author.id
        dt = DateFetcherFormatter.get_utc_date_time()
        day_of_week = dt.weekday()
        hour = dt.hour

        accounts = clashAccessData.getLinkedAccountsList(discord_id)

        if len(accounts) == 0:
            await discord_client.say('you must link accounts first!')
        else:

            await discord_client.say('Which accounts got free gifts today?')
            for i in range(len(accounts)):
                account = accounts[i]
                message = await discord_client.say('{}) {}\n'.format(i + 1, account))

                async def waitForResult(account, message, ctx):
                    await discord_client.add_reaction(message, config_strings.checkmark)
                    await discord_client.add_reaction(message, config_strings.xmark)

                    result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    if result.reaction.emoji == config_strings.checkmark:
                        result_string_temp = clashAccessData.setMemberFreeGiftDayAndTime(
                            account, day_of_week, hour, discord_id)
                        if result_string_temp == config_strings.success:
                            result_string = 'Set gift reminder for {}.'.format(
                                account)
                        else:
                            result_string = 'Failed to set gift reminder for {}.'.format(
                                account)
                        await discord_client.send_message(ctx.message.channel, result_string)

                discord_client.loop.create_task(waitForResult(account, message, ctx))

    @commands.command(name='start', pass_context=True,  brief='Connect your discord to a clash account')
    async def start(self, ctx):
        message_to_say = "Hi!\nI\'m clashBot and I am going to help you connect your Clash of Clans account to discord.\nSometimes, I\'ll ask you questions. Usually, you'll type a response, but sometimes I will let you hit a check ({}) for yes or an x ({}) for no. Sound good?".format(
            config_strings.checkmark, config_strings.xmark)
        message = await discord_client.say(message_to_say)
        await discord_client.add_reaction(message, config_strings.checkmark)
        await discord_client.add_reaction(message, config_strings.xmark)
        result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
        hit_check = (result.reaction.emoji == config_strings.checkmark)
        if hit_check:
            await discord_client.say('Great! Let\'s link your accounts now.')
            await account_management_cog.link_accounts_beta.callback(self, ctx)
        else:
            await discord_client.say('Ok, well since you hit the x, please let {} know what your problem with this is.'.format(leader_nickname))

    @commands.command(name='linkmemberaccount', pass_context=True,  brief='Connect your discord to a clash account')
    @commands.has_role("developers")
    async def link_accounts_for_member(self, ctx):
        await discord_client.say('Whose account would you like to link?')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        if len(message.mentions) > 0:
            discord_id = message.mentions[0].id
            await account_management_cog.link_accounts_beta.callback(self, ctx, discord_id)
            await account_management_cog.check_linked_accounts.callback(self, ctx, discord_id)
        else:
            await discord_client.say('Failed to find the mention')

    @commands.command(name='linkmyaccount', pass_context=True,  brief='Connect your discord to a clash account')
    async def link_accounts_beta(self, ctx, discord_id=None):
        """Link your Clash accounts to your discord account"""
        print('starting link')
        if discord_id is None:
            discord_id = ctx.message.author.id
        more_accounts_to_add = True
        successful_accounts = 0
        has_checked_if_should_refresh = False
        while more_accounts_to_add == True:
            await discord_client.say(' \n\nPlease enter your clash account name:')
            message = await discord_client.wait_for_message(author=ctx.message.author)
            member_name = message.content.upper()
            result = database_accessor.link_discord_account(discord_id, member_name, is_name=True)
            await discord_client.say(result)
            if result == config_strings.successfully_linked_string:
                successful_accounts += 1
                message = await discord_client.say("Do you have more clash accounts to add?\n")
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                more_accounts_to_add = (
                    result.reaction.emoji == config_strings.checkmark)
            elif result == config_strings.unable_to_find_account_string:
                hit_check = False
                if has_checked_if_should_refresh == False:
                    message = await discord_client.say("Was this account added to the clan in the last hour?")
                    await discord_client.add_reaction(message, config_strings.checkmark)
                    await discord_client.add_reaction(message, config_strings.xmark)
                    result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    hit_check = (result.reaction.emoji ==
                                 config_strings.checkmark)
                    has_checked_if_should_refresh = True
                if hit_check:
                    # force data update
                    await discord_client.say("Please wait while I refresh my data on the clan!")
                    time_checking = add_time_to_check()
                    while fetched_data_processor.previous_processed_time_instance.time < time_checking:
                        await asyncio.sleep(1)
                    await discord_client.say("Data has been refreshed. Enter the account name again in a moment when prompted.")
                else:
                    message = await discord_client.say("Do you want to try entering this account again? If you cannot find this account, please ask {}.".format(leader_nickname))
                    await discord_client.add_reaction(message, config_strings.checkmark)
                    await discord_client.add_reaction(message, config_strings.xmark)
                    result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    hit_check = (result.reaction.emoji ==
                                 config_strings.checkmark)
                    if not hit_check:
                        # no desire to continute

                        if successful_accounts > 0:
                            more_accounts_to_add = False
                        else:
                            await discord_client.say("Please let {} know that you were unable to resolve your issue.\n".format(leader_nickname))
                            return
            else:
                await discord_client.say("Please restart this command with !linkmyaccount\n")
                return

        # check if linked accounts contain one above TH 8
        allowed_to_donate = database_accessor.has_linked_account_with_th_larger_than(discord_id, config_options.minTHRequiredToBeADonator-1)

        if allowed_to_donate:

            has_configured_is_troop_donator = database_accessor.has_configured_is_troop_donator(discord_id)

            if not has_configured_is_troop_donator:
                message = await discord_client.say("Now that you have linked your account(s), would you like to become a troop donator? This means that during war, when people use the @troopdonator tag, you'll get a notification from discord, asking for troops.\n")
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                if result.reaction.emoji == config_strings.checkmark:
                    result_string = self.process_role_request(discord_id, 1)
                else:
                    result_string = self.process_role_request(discord_id, 0)
                await discord_client.say(result_string)

        general_channel = discord_client.get_channel(MyConfigBot.generalChannelID)
        bot_channel = discord_client.get_channel(MyConfigBot.testingChannelID)
        try:
            await update_roles(database_accessor)
            await discord_client.send_message(bot_channel, "Applied roles")
        except:
            await discord_client.send_message(bot_channel, "Failed to apply roles")

        introduction_string = 'Your account(s) are all set up!\n'
        introduction_string += 'During war, you may use @troopdonators to request troops for war.\n'
        rules_channel = server.get_channel(MyConfigBot.rulesChannelID)
        introduction_string += 'Please see {} for the clan rules.\n'.format(
            rules_channel.mention)
        war_channel = server.get_channel(MyConfigBot.warChannelID)
        introduction_string += 'Finally, we have a {} channel for discussing war.\n'.format(
            war_channel.mention)
        leader = server.get_member(MyConfigBot.leaderDiscordID)
        introduction_string += 'If you have any questions, please ask @{}!'.format(
            leader.nick)
        await discord_client.say(introduction_string)

    @commands.command(name='linkmyaccountold', hidden=True, pass_context=True,  brief='Connect your discord to a clash account')
    async def linkAccounts(self, ctx, *, member_name):
        member_name = member_name.upper()
        discord_id = ctx.message.author.id
        result = clashAccessData.link_discord_account(discord_id, member_name, is_name=True)
        await discord_client.say(result)

    @commands.command(name='linkmyaccountbytag', pass_context=True, hidden=True)
    async def linkAccountsWithTag(self, ctx, member_tag):
        discord_id = ctx.message.author.id
        result = clashAccessData.link_discord_account(discord_id, member_tag)
        await discord_client.say(result)

    @commands.command(name='checkmylinkedaccounts', pass_context=True,  brief='Check which clash accounts you have linked')
    async def check_linked_accounts(self, ctx, discord_id=None):
        """Check which Clash accounts are linked with your discord."""
        if discord_id is None:
            discord_id = ctx.message.author.id
        results = clashAccessData.getLinkedAccounts(discord_id)
        await discord_client.say(results)

    def process_role_request(self, discordID, val):
        result = clashAccessData.setTroopDonator(discordID, val)
        result_string = "You are now a troopdonator!"
        if val == 0:
            result_string = "You are now not a troopdonator."
        if result <= 0:
            result_string = "Unable to process request."

            # currently I don't ever hit this code block... do I want to?
            new_result = clashAccessData.checkTroopDonator(discordID, val)
            if new_result == True:
                if val == 1:
                    result_string = "You already had this role!"
                if val == 0:
                    result_string = "You didn't have this role anyways!"
        return result_string

    @commands.command(name='changemydonatorstatus', pass_context=True,  brief='Request to become or stop being a @troopdonator.')
    async def add_donator_role(self, ctx):

        message = await discord_client.say('Would you like to be a troopdonator?')

        discord_id = ctx.message.author.id

        await discord_client.add_reaction(message, config_strings.checkmark)
        await discord_client.add_reaction(message, config_strings.xmark)

        result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
        if result.reaction.emoji == config_strings.checkmark:
            want_to_be_donator = True
        else:
            want_to_be_donator = False

        result_string = self.process_role_request(discord_id, want_to_be_donator)
        await discord_client.send_message(ctx.message.channel, result_string)

        bot_channel = discord_client.get_channel(MyConfigBot.testingChannelID)
        try:
            await update_roles(database_accessor)
            await discord_client.send_message(bot_channel, "Applied roles")
        except:
            await discord_client.send_message(bot_channel, "Failed to apply roles")


#		await update_roles()

class ClanWar:

    @commands.command(name='lastroster', pass_context=True,  brief='See the last war roster')
    @commands.has_role("developers")
    async def get_clan_war_roster(self, ctx):
        await discord_client.say('Working on it...')
        timeChecking = add_time_to_check()
        while fetched_data_processor.previous_processed_time_instance.time < timeChecking:
            await asyncio.sleep(1)

        roster = clashAccessData.getMembersFromLastWar()
        await discord_client.say(roster)

    @commands.command(name='newroster', pass_context=True,  brief='See the new war roster with changes')
    @commands.has_role("coleaders")
    async def get_new_clan_war_roster(self, ctx):
        """Generate a new war roster with all changes that were requested."""
        await discord_client.say('Working on it...')
        timeChecking = add_time_to_check()
        while fetched_data_processor.previous_processed_time_instance.time < timeChecking:
            await asyncio.sleep(1)

        roster = clashAccessData.getNewWarRoster()
        await discord_client.say(roster)

    @commands.command(name='newrosternopull', pass_context=True,  brief='See the new war roster with changes')
    @commands.has_role("coleaders")
    async def getNewClanWarRoster2(self, ctx):
        """Generate a new war roster with all changes that were requested."""
        await discord_client.say('Working on it...')
        roster = clashAccessData.getNewWarRoster()
        await discord_client.say(roster)

    @commands.command(name='clearrosterchanges', pass_context=True,  brief='Remove all war roster changes')
    @commands.has_role("developers")
    async def clear_war_changes(self, ctx):
        clashAccessData.clearAddAndRemoveFromWar()
        await discord_client.say('done')

    @commands.command(name='undorosterchange', pass_context=True,  brief='Remove a specific war roster change')
    @commands.has_role("developers")
    async def undo_a_war_change(self, ctx):
        while True:
            changes = clashAccessData.getRosterChanges()
            await discord_client.say(changes)
            await discord_client.say('What change would you like to undo?')
            message = await discord_client.wait_for_message(author=ctx.message.author)
            change_number = int(message.content)
            result = clashAccessData.undoWarChange(int(change_number))
            await discord_client.say('{} changes made'.format(result))

            message = await discord_client.say('Would you like to undo another change?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discord_client.send_message(ctx.message.channel, resultString)

    @commands.command(name='seerosterchanges', pass_context=True,  brief='See all war roster changes for the next war')
    async def see_war_changes(self, ctx):
        results = clashAccessData.getRosterChanges()
        await discord_client.say(results)

    @commands.command(name='removememberfromwar', pass_context=True,  brief='Remove someone else from war')
    @commands.has_role("developers")
    async def remove_from_war(self, ctx):
        while True:
            await discord_client.say('Who would you like to remove from war?')
            message = await discord_client.wait_for_message(author=ctx.message.author)

            clash_account_name = message.content.upper()
            result = clashAccessData.removeMemberFromWar(clash_account_name)
            await discord_client.say(result)

            message = await discord_client.say('Would you like to remove someone else from war?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discord_client.send_message(ctx.message.channel, resultString)

    @commands.command(name='addmembertowar', pass_context=True,  brief='Add someone else to war')
    @commands.has_role("developers")
    async def add_to_war(self, ctx):
        while True:
            await discord_client.say('Who would you like to add to war?')
            message = await discord_client.wait_for_message(author=ctx.message.author)

            clash_account_name = message.content.upper()
            result = clashAccessData.addMemberToWar(clash_account_name)
            await discord_client.say(result)

            message = await discord_client.say('Would you like to add someone else to war?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break

    @commands.command(name='checkmypastwarperformance', pass_context=True,  brief="Check member's past war performance")
    @commands.has_role("developers")
    async def check_my_past_war_performance(self, ctx):
        discord_id = ctx.message.author.id
        results_dict = clashAccessData.getPastWarPerformance(discord_id, 5)
        results = clashConvertDataToString.convert_war_attacks_to_string(
            results_dict)
        try:
            await discord_client.say(results)
        except:
            await discord_client.say('error sending')

    @commands.command(name='checkmemberpastwarperformance', pass_context=True,  brief="Check member's past war performance")
    @commands.has_role("developers")
    async def check_member_past_war_performance(self, ctx, number_of_wars=5):
        while True:
            await discord_client.say('Who would you like to see the past performance of?')
            message = await discord_client.wait_for_message(author=ctx.message.author)

            clashAccountName = message.content.upper()
            try:
                resultDict = clashAccessData.getPastWarPerformanceForMemberName(
                    clashAccountName, number_of_wars)
                result_string = clashConvertDataToString.convert_war_attacks_to_string(
                    resultDict)
            except ValueError as e:
                result_string = e
            try:
                await discord_client.say(result_string)
            except:
                await discord_client.say('error sending')

            message = await discord_client.say('Would you like to check someone else?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break

    @commands.command(name='changemywarstatus', pass_context=True,  brief='Change your war status')
    @commands.has_role("has_war_permissions")
    async def change_war_status(self, ctx):
        discord_id = ctx.message.author.id

        # get accounts currently in clan
        accounts = clashAccessData.getLinkedAccountsList(
            discord_id, currently_in_clan_required=True)

        if len(accounts) == 0:
            await discord_client.say('you must link accounts first!')
        else:
            question = 'Please hit the check on any accounts you want to add to war, and the x on any you want to remove from war.'
            await discord_client.say(question)
            for i in range(len(accounts)):
                account = accounts[i]

                message = await discord_client.say('{}) {}\n'.format(i + 1, account))

                async def wait_for_result(account, message, ctx):

                    await discord_client.add_reaction(message, config_strings.checkmark)
                    await discord_client.add_reaction(message, config_strings.xmark)

                    result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    if result.reaction.emoji == config_strings.checkmark:
                        result_string_temp = clashAccessData.addMemberToWar(
                            account)
                        if result_string_temp == config_strings.success:
                            result_string = '{} added to war'.format(account)
                        else:
                            result_string = 'Failed to add {} to war'.format(
                                account)
                    else:
                        result_string_temp = clashAccessData.removeMemberFromWar(
                            account)
                        if result_string_temp == config_strings.success:
                            result_string = '{} removed from war'.format(
                                account)
                        else:
                            result_string = 'Failed to remove {} from war'.format(
                                account)
                    await discord_client.send_message(ctx.message.channel, result_string)

                discord_client.loop.create_task(wait_for_result(account, message, ctx))


class ClanGames:
    @commands.command(name='checkmyCGscores', pass_context=True,  brief='Check your recent Clan Games scores')
    async def check_my_cg_scores(self, ctx):
        discord_id = ctx.message.author.id
        results = clashAccessData.getClanGamesResultsFor(discord_id)
        await discord_client.say(results)

    @commands.command(name='checkmemberCGscores', pass_context=True,  brief='Check other members Clan Games scores')
    @commands.has_role("developers")
    async def check_members_cg_scores(self, ctx):

        while True:
            await discord_client.say('Who would you like to get Clan Games scores for?')
            message = await discord_client.wait_for_message(author=ctx.message.author)
            member_name = message.content.upper()
            results = clashAccessData.getClanGamesResultsForMemberName(
                member_name)
            await discord_client.say(results)

            message = await discord_client.say('Would you like to check another account?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                continue
            else:
                break
            await discord_client.send_message(ctx.message.channel, resultString)

    @commands.command(name='checklowCGscores', pass_context=True,  brief='Get members underperforming in the clan games.')
    @commands.has_role("developers")
    async def getClanGamesScores(self, ctx, threshold=250):
        await discord_client.say('Working on it...')
        roster = clashAccessData.getMembersWithScoreUnderThreshold(threshold)
        await discord_client.say(roster)

    @commands.command(name='checkineligibleforCG', pass_context=True,  brief='Get members that are too low TH for the CGs.')
    @commands.has_role("developers")
    async def getIneligibleTHs(self, ctx):
        roster = clashAccessData.getIneligibleForClanGames()
        await discord_client.say(roster)


class ClanManagement:
    @commands.command(name='trackdonations', pass_context=True)
    @commands.has_role("developers")
    async def track_bad_donations(self, ctx):
        discord_id = ctx.message.author.id
        await discord_client.say('How long ago was the request made, in minutes? (Over estimate if needed)')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        current_timestamp = DateFetcherFormatter.get_utc_timestamp()
        time_since_created = current_timestamp - int(message.content) * 60
        await discord_client.say('How long ago was the request filled, in minutes? (Under estimate if needed, 0 if necessary)')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        time_since_filled = current_timestamp - int(message.content) * 60

        if time_since_filled > fetched_data_processor.previous_processed_time_instance.time:
            time_checking = add_time_to_check()
            while fetched_data_processor.previous_processed_time_instance.time < time_checking:
                await asyncio.sleep(1)

        result_dict = clashAccessData.getAllDonatedOrReceivedInTimeFrame(time_since_created, time_since_filled)
        result_string = clashConvertDataToString.convert_donation_timeframe_results(result_dict)
        await discord_client.say(str(result_dict))
        await discord_client.say(result_string)

    @commands.command(name='getallmemberswithoutdiscord', pass_context=True)
    @commands.has_role("developers")
    async def get_all_members_without_discord(self, ctx):
        discord_id = ctx.message.author.id
        results = database_accessor.get_all_members_without_discord_as_string()
        await discord_client.say(results)

    @commands.command(name='getwarmemberswithoutdiscord', pass_context=True)
    @commands.has_role("developers")
    async def get_war_members_without_discord(self, ctx):
        discord_id = ctx.message.author.id
        results = database_accessor.getMembersInWarWithoutDiscordAsString()
        await discord_client.say(results)

    @commands.command(name='linkothersaccount', pass_context=True)
    @commands.has_role("developers")
    async def linkOthersAccounts(self, ctx, discordID, member_name):
        """Allows developer to provide a discord id and membername to link an account, should use linkmemberaccount instead"""
        member_name = member_name.upper()
        result = clashAccessData.link_discord_account(discordID, member_name, is_name=True)
        await discord_client.say(result)

    @commands.command(name='seealllinkedaccounts', pass_context=True)
    @commands.has_role("developers")
    async def see_all_linked_accounts(self, ctx):
        result = clashAccessData.getAllLinkedAccountsList()
        await discord_client.say(result)

    @commands.command(name='remindtostart', pass_context=True)
    @commands.has_role("developers")
    async def remindToStart(self, ctx):
        await discord_client.say('Who would you like to remind to setup their account?')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        if len(message.mentions) > 0:
            discord_id = message.mentions[0]
            await discord_client.on_member_join(discord_id)
        else:
            await discord_client.say('Failed to find the mention')

    @commands.command(name='givememberwarpermissions', pass_context=True)
    @commands.has_role("developers")
    async def give_member_war_permissions(self, ctx):
        discordID = ctx.message.author.id
        await discord_client.say('Who would you like to set war permissions for?')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        member_name = message.content.upper()
        account_exists = clashAccessData.verifyAccountExists(member_name)
        if account_exists:
            message = await discord_client.say('Should this account have permissions?')
            await discord_client.add_reaction(message, config_strings.checkmark)
            await discord_client.add_reaction(message, config_strings.xmark)

            result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
            if result.reaction.emoji == config_strings.checkmark:
                count = clashAccessData.setWarPermissionVal(member_name, 1)
            else:
                count = clashAccessData.setWarPermissionVal(member_name, 0)
            await discord_client.say('{} rows changed.'.format(count))
            try:
                await update_roles(database_accessor)
                await discord_client.say("Applied roles")
            except:
                await discord_client.say("Failed to apply roles")
        else:
            await discord_client.say('Unable to find this account')


clan_war_clog = ClanWar()
discord_client.add_cog(clan_war_clog)

clan_management_cog = ClanManagement()
discord_client.add_cog(clan_management_cog)

clan_games_cog = ClanGames()
discord_client.add_cog(clan_games_cog)

account_management_cog = AccountManagement()
discord_client.add_cog(account_management_cog)


async def update_roles(database_accessor):

    print('updating roles')
    roles = server.roles

    def find(f, seq):
        """Return first item in sequence where f(item) == True."""
        for item in seq:
            if f(item):
                return item
        return None
    member_role = find(lambda role: role.name == 'members', roles)
    war_role = find(lambda role: role.name == 'war', roles)
    troop_role = find(lambda role: role.name == 'troopdonators', roles)
    check_in_role = find(lambda role: role.name == 'MIAUsers', roles)
    war_perms_role = find(lambda role: role.name == 'has_war_permissions', roles)
    th12_role = find(lambda role: role.name == 'TH12', roles)

    discord_ids_of_members_in_clan = database_accessor.get_members_in_clan()
    discord_ids_of_war_participants = database_accessor.get_discord_members_in_war()
    discord_ids_of_members_with_war_permissions = database_accessor.get_discord_ids_of_members_with_war_permissions()
    discord_ids_of_members_who_are_th12 = database_accessor.get_discord_ids_of_members_who_are_th12()

    print(discord_ids_of_members_in_clan)
    print(discord_ids_of_war_participants)
    print(discord_ids_of_members_with_war_permissions)
    print(discord_ids_of_members_who_are_th12)

    # go through everyone in discord
    for server_member in server.members:

        if server_member.bot:
            continue
        server_member_id = server_member.id

        if server_member_id in discord_ids_of_members_in_clan:
            roles_to_add = []
            roles_to_remove = []

            if member_role not in server_member.roles:
                roles_to_add.append(member_role)

            is_troop_donator = discord_ids_of_members_in_clan[server_member_id]
            if is_troop_donator == 1:
                if troop_role not in server_member.roles:
                    roles_to_add.append(troop_role)
            else:
                if troop_role in server_member.roles:
                    roles_to_remove.append(troop_role)

            if server_member_id in discord_ids_of_members_with_war_permissions:
                if war_perms_role not in server_member.roles:
                    roles_to_add.append(war_perms_role)
            else:
                if war_perms_role in server_member.roles:
                    roles_to_remove.append(war_perms_role)

            if server_member_id in discord_ids_of_war_participants:
                if war_role not in server_member.roles:
                    roles_to_add.append(war_role)
            else:
                if war_role in server_member.roles:
                    roles_to_remove.append(war_role)

            if server_member_id in discord_ids_of_members_who_are_th12:
                if th12_role not in server_member.roles:
                    roles_to_add.append(th12_role)
            else:
                if th12_role in server_member.roles:
                    roles_to_remove.append(th12_role)

            # update roles
            if len(roles_to_add) > 0:
                await discord_client.add_roles(server_member, *roles_to_add)
            if len(roles_to_remove) > 0:
                for role in roles_to_remove:
                    print(role)
                await discord_client.remove_roles(server_member, *roles_to_remove)
        # if not in clan, remove roles
        else:
            if len(server_member.roles) > 1:
                await discord_client.remove_roles(server_member, member_role, war_role, troop_role, check_in_role)

    print('done updating!')


def update_times_to_check_data():

    current_date_time = DateFetcherFormatter.get_utc_date_time()
    print('current:           {}'.format(current_date_time.timestamp()))

    current_rounded_down_to_hour_and5 = datetime.datetime(
        current_date_time.year, current_date_time.month, current_date_time.day, current_date_time.hour, 5).replace(tzinfo=pytz.utc)
    print('currentRoundedDown {}'.format(
        current_rounded_down_to_hour_and5.timestamp()))

    if current_date_time < current_rounded_down_to_hour_and5:
        next_time_to_check_data = current_rounded_down_to_hour_and5.timestamp()
    else:
        next_hour_and5 = current_rounded_down_to_hour_and5.timestamp() + (60 * 60)
        print('5pastnexthour      {}'.format(next_hour_and5))
        next_time_to_check_data = next_hour_and5
    print('nextTime:          {}'.format(next_time_to_check_data))

#	current_date_time = datetime.datetime.utcnow()
#	currentRoundedDownToHour = datetime.datetime(current_date_time.year, current_date_time.month, current_date_time.day, current_date_time.hour)
#	currentRoundedDownToHourSeconds = currentRoundedDownToHour.replace(tzinfo=pytz.utc).timestamp() + 300
#	nextRoundedDownToHourSeconds = currentRoundedDownToHourSeconds + (60 * 60)
#	if currentRoundedDownToHourSeconds not in times_to_check_data and lastFetchedData < currentRoundedDownToHourSeconds:
#		times_to_check_data.append(currentRoundedDownToHourSeconds)
#	if nextRoundedDownToHourSeconds not in times_to_check_data and lastFetchedData < nextRoundedDownToHourSeconds:
#		times_to_check_data.append(nextRoundedDownToHourSeconds)
#
#	times_to_check_data.sort()
#
# print("current:")
#	currentTimeEpoch = current_date_time.replace(tzinfo=pytz.utc).timestamp()
# print(currentTimeEpoch)
# print("list:")
# for entry in times_to_check_data:
# print(entry)
#
    return next_time_to_check_data


times_to_check_data = []

data_check_override = False

def add_time_to_check():
    #	if timestampTest == None:
    timestampTest = DateFetcherFormatter.get_utc_timestamp()
#	global times_to_check_data
#	times_to_check_data.append(timestampTest)
    global data_check_override
    data_check_override = True

    return timestampTest


async def send_out_gift_reminders(database_accessor):
    return
    bot_channel = discord_client.get_channel(botChannelID)
    general_channel = discord_client.get_channel(MyConfigBot.generalChannelID)

    while True:
        current_date_time = DateFetcherFormatter.get_utc_date_time()
        current_date_time_timestamp = int(current_date_time.timestamp())
        accounts_with_gifts_on_it = clashAccessData.getAccountsWhoGetGiftReminders(
            current_date_time)
        for entry in accounts_with_gifts_on_it:
            discord_id = str(entry['discord'])
            account_name = entry['account_name']
            member = server.get_member(discord_id)
            await discord_client.send_message(bot_channel, 'Hey {}, {} gets a free gift today!'.format(member.mention, account_name))
            await asyncio.sleep(1)
        next_timestamp = current_date_time_timestamp + 3600
        time_to_sleep = next_timestamp - current_date_time_timestamp
        await asyncio.sleep(time_to_sleep)


async def send_out_war_reminders(database_accessor):
    war_channel = discord_client.get_channel(MyConfigBot.warChannelID)
    bot_channel = discord_client.get_channel(MyConfigBot.testingChannelID)
    while True:
        next_timestamps_for_war = database_accessor.get_timestamps_for_current_war()
        if next_timestamps_for_war is None:
            await asyncio.sleep(3600*6)
        else:
            next_war_timestamp = next_timestamps_for_war[0][0]
            next_war_timestamp_string = next_timestamps_for_war[0][1]
            time_to_sleep = next_war_timestamp - DateFetcherFormatter.get_utc_timestamp()
            await asyncio.sleep(time_to_sleep)

            # update data to be sure we aren't sending reminders to people who have already attacked, just recently
            time_checking = add_time_to_check()
            while fetched_data_processor.previous_processed_time_instance.time < time_checking:
                await asyncio.sleep(1)

            accounts_that_need_to_attack = database_accessor.get_members_in_war_with_attacks_remaining()
            for discord_id in accounts_that_need_to_attack:
                account_names_dict = accounts_that_need_to_attack[discord_id]
                account_names_string = ""
                accounts_total = len(account_names_dict)
                current_account = 0
                for account_name in account_names_dict:
                    number_of_attacks = account_names_dict[account_name]
                    if number_of_attacks == 1:
                        account_names_string += ' your {} attack with {}'.format(
                            number_of_attacks, account_name)
                    else:
                        account_names_string += ' your {} attacks with {}'.format(
                            number_of_attacks, account_name)
                    if current_account == accounts_total - 1:
                        # last account, do nothing at the end
                        account_names_string += ''
                    elif current_account == accounts_total - 2 and accounts_total == 2:
                        account_names_string += ' and'
                    elif current_account == accounts_total - 2:
                        account_names_string += ', and'
                    else:
                        account_names_string += ','
                    current_account += 1
                discord_id = str(discord_id)
                member = server.get_member(discord_id)
                await discord_client.send_message(war_channel, 'Hey {}, make sure to use{}! {}'.format(member.mention, account_names_string, next_war_timestamp_string))
                await asyncio.sleep(1)


async def createRules():
    rules_channel = discord_client.get_channel(MyConfigBot.rulesChannelID)
    with open('clanRules.json') as rulesFiles:
        new_rules = json.load(rulesFiles)
        # Most of the time, we will be modifying wording, so we want to delete and re-enter the same number of rules.
        # We can always manually delete 1 or 2 extra manually if we delete rule categories.
        async for x in discord_client.logs_from(rules_channel, limit=len(new_rules["Rules"])):
            await discord_client.delete_message(x)
        for x in new_rules["Rules"]:
            x['type'] = 'rich'
            new_embed = discord.Embed(**x)
            await discord_client.send_message(rules_channel, embed=new_embed)


async def start_gathering_data():

    print('start_gathering_data starting')

    global times_to_check_data
    # global last_updated_data
    global data_check_override

    db_path = "clashData.db"
    db_session = DatabaseSetup.get_session(engine_string="sqlite:///" + db_path)

# self.previous_processed_time
#     last_updated_data = fetched_data_processor.previous_processed_time # clashAccessData.getLastProcessedTime()

    # this is last retrieved, regardless of failure
    # last_fetched = clashAccessData.getLastProcessedTime()

    # this handles startups, but prevents spammy startups when restarting several times in a row
    if DateFetcherFormatter.get_utc_timestamp() - fetched_data_processor.previous_processed_time_instance.time > 60 * 60:
        data_check_override = True

    await discord_client.wait_until_ready()
    bot_channel = discord_client.get_channel(botChannelID)

    global server
    server = discord_client.get_server(MyConfigBot.server_id)

    discord_client.loop.create_task(send_out_gift_reminders(database_accessor))
    # discord_client.loop.create_task(send_out_war_reminders(database_accessor))
    # discord_client.loop.create_task(createRules())

    await discord_client.send_message(bot_channel, "Coming online")

    next_time_to_check_data = update_times_to_check_data()
    try:
        while True:
            current_time_seconds = int(time.time())
#			print("\n\nUpdating")

            if data_check_override == True:
                pass
            elif current_time_seconds >= next_time_to_check_data:
                next_time_to_check_data = update_times_to_check_data()
                pass
            else:
                await asyncio.sleep(1)
                continue

            print('got here...')

            last_fetched = DateFetcherFormatter.get_utc_timestamp()
            data_check_override = False

            print("getting data")
            try:
                await discord_client.send_message(bot_channel, "Getting data")
                try:
                    await discord_client.loop.run_in_executor(None, data_fetcher.get_data_from_server)
                    # data_fetcher.get_data_from_server()
                    await asyncio.sleep(1)
                except Exception as e:
                    await discord_client.send_message(bot_channel, "get_data_from_server: {}".format(e))
                    raise
                try:
                    data_valid = await discord_client.loop.run_in_executor(None, data_fetcher.validate_data)
                    data_valid = data_fetcher.validate_data()
                except IOError as e:
                    await discord_client.send_message(bot_channel, "The data file doesn't exist to validate {}".format(e))
                    data_valid = False
            except Exception as e:
                print(e)
                await discord_client.send_message(bot_channel, "error, trying again momentarily")
                await asyncio.sleep(60)
                try:
                    await discord_client.send_message(bot_channel, "trying again now")
                    await discord_client.loop.run_in_executor(None, data_fetcher.get_data_from_server)
                    data_fetcher.get_data_from_server()
                    data_valid = await discord_client.loop.run_in_executor(None, data_fetcher.validate_data)
                    data_valid = data_fetcher.validate_data()
                except:
                    await discord_client.send_message(bot_channel, "Something is not working")
                    data_valid = False
            if data_valid:
                await discord_client.send_message(bot_channel, "Data was retrieved")
                try:
                    # await discord_client.loop.run_in_executor(None, fetched_data_processor.save_data)
                    fetched_data_processor.save_data()
                    await asyncio.sleep(1)
                    # last_updated_data = DateFetcherFormatter.get_utc_timestamp()
                    await discord_client.send_message(bot_channel, "Data was saved")
                    try:
                        await update_roles(database_accessor)
                        await discord_client.send_message(bot_channel, "Applied roles")
                    except Exception:
                        await discord_client.send_message(bot_channel, "Failed to apply roles")
                except:
                    await discord_client.send_message(bot_channel, "Data failed to save")
            else:
                await discord_client.send_message(bot_channel, "Data was not retrieved")

    except Exception as err:
        print("Error: " + str(err))

discord_client.loop.create_task(start_gathering_data())

discordToken = MyConfigBot.token
discord_client.run(discordToken)
