# -*- coding: utf-8 -*-

import discord
import asyncio
import time
import datetime
import pytz
from discord.ext import commands
#import clashWebServer
from ClashBot import FetchedDataProcessor, DatabaseAccessor, DateFetcherFormatter, SupercellDataFetcher, FetchedDataProcessorHelper, NoActiveClanWarLeagueWar, NoActiveClanWar, TraderAccountNotConfigured, TraderInvalidInput, TraderAccountNotConfigured, ContentCreator
from my_help_formatter import MyHelpFormatter, _default_help_command
# import clashAccessData
import config_strings
# from MyHelpFormatter import , _default_help_command
import json

from ClashBot import session_scope

import traceback

with open("configs/discord.json") as infile:
    discord_config = json.load(infile)

# make this come from config
botChannelID = discord_config["testingChannelID"]
generalChannelID = discord_config["generalChannelID"]
rulesChannelID = discord_config["rulesChannelID"]
testingChannelID = discord_config["testingChannelID"]
warChannelID = discord_config["warChannelID"]
leaderDiscordID = discord_config["leaderDiscordID"]
server_id = discord_config["server_id"]
token = discord_config["token"]
leader_nickname = discord_config["leader_nickname"]

with open("configs/app.json") as infile:
    app_config = json.load(infile)
min_th_required_to_donate_troops = app_config["min_th_required_to_donate_troops"]

discord_client = commands.Bot(command_prefix='!', formatter=MyHelpFormatter())
discord_client.remove_command('help')
discord_client.command(**discord_client.help_attrs)(_default_help_command)

server = None
last_updated_data_time = 0


class MemberDoesNotExistException(Exception):
    pass


class MemberNotSelectedException(Exception):
    pass


@discord_client.event
async def on_member_join(member):
    """Says when a member joined."""
    msg = 'Hi {0.mention}! Please set up your account by typing: !start (including the exclamation point)'.format(member)
    general_channel = discord_client.get_channel(generalChannelID)
    # botChannel = discord_client.get_channel(testingChannelID)
    await discord_client.send_message(general_channel, msg)


@discord_client.event
async def on_member_remove(member):
    """Says when a member leaves/was kicked."""
    msg = '{0.mention} has left the server'.format(member)
    # generalChannel = discord_client.get_channel(generalChannelID)
    bot_channel = discord_client.get_channel(testingChannelID)
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
    while last_updated_data_time < time_checking:
        await asyncio.sleep(1)


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def save(ctx):
    with session_scope() as session:
        fetched_data_processor = FetchedDataProcessor(session)
        fetched_data_processor.save_data()
        await discord_client.say('Saved')

@discord_client.command(name="updateroles", pass_context=True)
@commands.has_role("developers")
async def update_roles_command(ctx):
    try:
        bot_channel = discord_client.get_channel(botChannelID)
        await update_roles()
        await discord_client.send_message(bot_channel, "Applied roles")
        try:
            await notify_if_cwl_roster_needs_set()
            await discord_client.send_message(bot_channel, "Notified that CWL roster needs set (if it does)")
            await discord_client.say('Updated')
        except Exception:
            await discord_client.send_message(bot_channel, "Failed to notify that CWL needs set")
    except Exception:
        await discord_client.send_message(bot_channel, "Failed to apply roles")


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def error(ctx):
    raise ValueError('Some error!')
    await discord_client.say('Threw error?')

@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def updatesupercellkey(ctx):

    await discord_client.say('Paste your key here:')
    message = await discord_client.wait_for_message(author=ctx.message.author)

    try:
        supercell_key = message.content.strip()

        with open("configs/supercell.json") as supercell_config_file:
            supercell_config = json.load(supercell_config_file)

        supercell_config["supercell_token_to_use"] = supercell_key

        with open("configs/supercell.json", "w") as outfile:
            json.dump(supercell_config, outfile)

        await discord_client.say('Done.')
    except:
        await discord_client.say('Failed.')


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def say(ctx):

    await discord_client.say('What channel would you like me to talk in?')
    message = await discord_client.wait_for_message(author=ctx.message.author)

    if len(message.channel_mentions) > 0:
        channel_to_send_to = message.channel_mentions[0]
        await discord_client.say('What would you like to say?')
        message = await discord_client.wait_for_message(author=ctx.message.author)
        await discord_client.send_message(channel_to_send_to, message.content)
    else:
        await discord_client.say('Failed to find the mention')


@discord_client.command(pass_context=True)
@commands.has_role("developers")
async def clear(ctx):

    await discord_client.say('How many messages should I delete (max of 98)?')
    message = await discord_client.wait_for_message(author=ctx.message.author)
    amount = int(message.content) + 3
    await discord_client.purge_from(ctx.message.channel, limit=amount)


class AccountManagement:

    # @commands.command(name='removeaccountsrelatedto', pass_context=True)
    # @commands.has_role("developers")
    # async def remove_discord_accounts_related_to(self, ctx, *, account_name):
    #       """
    #       This function takes a clash account name and disassociates it from all discord accounts it's linked with
    #       """
    #     account_name = account_name.upper()
    #     results = clashAccessData.remove_discord_accounts_related_to(account_name)
    #     await discord_client.say('{} removed.'.format(results))

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
    @commands.has_role("developers_dontexist")
    async def link_accounts_beta(self, ctx, discord_id=None):
        """Link your Clash accounts to your discord account. No reason to ever call this, always called via start"""
        print('starting link')
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
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
                        hit_check = (result.reaction.emoji == config_strings.checkmark)
                        has_checked_if_should_refresh = True
                    if hit_check:
                        # force data update
                        await discord_client.say("Please wait while I refresh my data on the clan!")
                        time_checking = add_time_to_check()
                        while last_updated_data_time < time_checking:
                            await asyncio.sleep(1)
                        await discord_client.say("Data has been refreshed. Enter the account name again in a moment when prompted.")
                    else:
                        message = await discord_client.say("Do you want to try entering this account again? If you cannot find this account, please ask {}.".format(leader_nickname))
                        await discord_client.add_reaction(message, config_strings.checkmark)
                        await discord_client.add_reaction(message, config_strings.xmark)
                        result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                        hit_check = (result.reaction.emoji == config_strings.checkmark)
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
            allowed_to_donate = database_accessor.has_linked_account_with_th_larger_than(discord_id, min_th_required_to_donate_troops-1)

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

        general_channel = discord_client.get_channel(generalChannelID)
        bot_channel = discord_client.get_channel(testingChannelID)
        try:
            await update_roles()
            await discord_client.send_message(bot_channel, "Applied roles")
        except:
            await discord_client.send_message(bot_channel, "Failed to apply roles")

        introduction_string = 'Your account(s) are all set up!\n'
        introduction_string += 'During war, you may use @troopdonators to request troops for war.\n'
        rules_channel = server.get_channel(rulesChannelID)
        introduction_string += 'Please see {} for the clan rules.\n'.format(rules_channel.mention)
        war_channel = server.get_channel(warChannelID)
        introduction_string += 'Finally, we have a {} channel for discussing war.\n'.format(war_channel.mention)
        leader = server.get_member(leaderDiscordID)
        introduction_string += 'If you have any questions, please ask @{}!'.format(leader.nick)
        await discord_client.say(introduction_string)

    # @commands.command(name='linkmyaccountold', hidden=True, pass_context=True,  brief='Connect your discord to a clash account')
    # async def linkAccounts(self, ctx, *, member_name):
    #     member_name = member_name.upper()
    #     discord_id = ctx.message.author.id
    #     result = clashAccessData.link_discord_account(discord_id, member_name, is_name=True)
    #     await discord_client.say(result)

    # @commands.command(name='linkmyaccountbytag', pass_context=True, hidden=True)
    # async def linkAccountsWithTag(self, ctx, member_tag):
    #     discord_id = ctx.message.author.id
    #     result = clashAccessData.link_discord_account(discord_id, member_tag)
    #     await discord_client.say(result)

    @commands.command(name='checkmylinkedaccounts', pass_context=True,  brief='Check which clash accounts you have linked')
    async def check_linked_accounts(self, ctx, discord_id=None):
        """Check which Clash accounts are linked with your discord."""
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            if discord_id is None:
                discord_id = ctx.message.author.id
            results = database_accessor.get_linked_accounts(discord_id)
            if len(results) == 0:
                await discord_client.say("No linked accounts")
                return
            output = "You own these:\n"
            for member in results:
                output += member.member_name + "\n"
            await discord_client.say(output)

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
    @commands.has_role("developers")
    async def add_donator_role(self, ctx):
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
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

            bot_channel = discord_client.get_channel(testingChannelID)
            try:
                await update_roles()
                await discord_client.send_message(bot_channel, "Applied roles")
            except:
                await discord_client.send_message(bot_channel, "Failed to apply roles")

class ClanWar:

    @commands.command(name='lastroster', pass_context=True,  brief='See the last war roster')
    @commands.has_role("developers")
    async def get_clan_war_roster(self, ctx):
        await discord_client.say('Working on it...')
        roster = clashAccessData.getMembersFromLastWar()
        await discord_client.say(roster)

    # @commands.command(name='newroster', pass_context=True,  brief='See the new war roster with changes')
    # @commands.has_role("developers")
    # async def get_new_clan_war_roster(self, ctx):
    #     """Generate a new war roster with all changes that were requested."""
    #     await discord_client.say('Working on it...')
    #     timeChecking = add_time_to_check()
    #     while last_updated_data_time < timeChecking:
    #         await asyncio.sleep(1)
    #
    #     roster = clashAccessData.getNewWarRoster()
    #     await discord_client.say(roster)
    #
    # @commands.command(name='newrosternopull', pass_context=True,  brief='See the new war roster with changes')
    # @commands.has_role("developers")
    # async def getNewClanWarRoster2(self, ctx):
    #     """Generate a new war roster with all changes that were requested."""
    #     await discord_client.say('Working on it...')
    #     roster = clashAccessData.getNewWarRoster()
    #     await discord_client.say(roster)
    #
    # @commands.command(name='clearrosterchanges', pass_context=True,  brief='Remove all war roster changes')
    # @commands.has_role("developers")
    # async def clear_war_changes(self, ctx):
    #     clashAccessData.clearAddAndRemoveFromWar()
    #     await discord_client.say('done')
    #
    # @commands.command(name='undorosterchange', pass_context=True,  brief='Remove a specific war roster change')
    # @commands.has_role("developers")
    # async def undo_a_war_change(self, ctx):
    #     while True:
    #         changes = clashAccessData.getRosterChanges()
    #         await discord_client.say(changes)
    #         await discord_client.say('What change would you like to undo?')
    #         message = await discord_client.wait_for_message(author=ctx.message.author)
    #         change_number = int(message.content)
    #         result = clashAccessData.undoWarChange(int(change_number))
    #         await discord_client.say('{} changes made'.format(result))
    #
    #         message = await discord_client.say('Would you like to undo another change?')
    #         await discord_client.add_reaction(message, config_strings.checkmark)
    #         await discord_client.add_reaction(message, config_strings.xmark)
    #
    #         result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #         if result.reaction.emoji == config_strings.checkmark:
    #             continue
    #         else:
    #             break
    #         await discord_client.send_message(ctx.message.channel, resultString)
    #
    # @commands.command(name='seerosterchanges', pass_context=True,  brief='See all war roster changes for the next war')
    # @commands.has_role("developers")
    # async def see_war_changes(self, ctx):
    #     results = clashAccessData.getRosterChanges()
    #     await discord_client.say(results)
    #
    # @commands.command(name='removememberfromwar', pass_context=True,  brief='Remove someone else from war')
    # @commands.has_role("developers")
    # async def remove_from_war(self, ctx):
    #     while True:
    #         await discord_client.say('Who would you like to remove from war?')
    #         message = await discord_client.wait_for_message(author=ctx.message.author)
    #
    #         clash_account_name = message.content.upper()
    #         result = clashAccessData.removeMemberFromWar(clash_account_name)
    #         await discord_client.say(result)
    #
    #         message = await discord_client.say('Would you like to remove someone else from war?')
    #         await discord_client.add_reaction(message, config_strings.checkmark)
    #         await discord_client.add_reaction(message, config_strings.xmark)
    #
    #         result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #         if result.reaction.emoji == config_strings.checkmark:
    #             continue
    #         else:
    #             break
    #         await discord_client.send_message(ctx.message.channel, resultString)
    #
    # @commands.command(name='addmembertowar', pass_context=True,  brief='Add someone else to war')
    # @commands.has_role("developers")
    # async def add_to_war(self, ctx):
    #     while True:
    #         await discord_client.say('Who would you like to add to war?')
    #         message = await discord_client.wait_for_message(author=ctx.message.author)
    #
    #         clash_account_name = message.content.upper()
    #         result = clashAccessData.addMemberToWar(clash_account_name)
    #         await discord_client.say(result)
    #
    #         message = await discord_client.say('Would you like to add someone else to war?')
    #         await discord_client.add_reaction(message, config_strings.checkmark)
    #         await discord_client.add_reaction(message, config_strings.xmark)
    #
    #         result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #         if result.reaction.emoji == config_strings.checkmark:
    #             continue
    #         else:
    #             break
    #
    # @commands.command(name='checkmypastwarperformance', pass_context=True,  brief="Check member's past war performance")
    # @commands.has_role("developers")
    # async def check_my_past_war_performance(self, ctx):
    #     discord_id = ctx.message.author.id
    #     results_dict = clashAccessData.getPastWarPerformance(discord_id, 5)
    #     results = clashConvertDataToString.convert_war_attacks_to_string(
    #         results_dict)
    #     try:
    #         await discord_client.say(results)
    #     except:
    #         await discord_client.say('error sending')
    #
    # @commands.command(name='checkmemberpastwarperformance', pass_context=True,  brief="Check member's past war performance")
    # @commands.has_role("developers")
    # async def check_member_past_war_performance(self, ctx, number_of_wars=5):
    #     while True:
    #         await discord_client.say('Who would you like to see the past performance of?')
    #         message = await discord_client.wait_for_message(author=ctx.message.author)
    #
    #         clashAccountName = message.content.upper()
    #         try:
    #             resultDict = clashAccessData.getPastWarPerformanceForMemberName(
    #                 clashAccountName, number_of_wars)
    #             result_string = clashConvertDataToString.convert_war_attacks_to_string(
    #                 resultDict)
    #         except ValueError as e:
    #             result_string = e
    #         try:
    #             await discord_client.say(result_string)
    #         except:
    #             await discord_client.say('error sending')
    #
    #         message = await discord_client.say('Would you like to check someone else?')
    #         await discord_client.add_reaction(message, config_strings.checkmark)
    #         await discord_client.add_reaction(message, config_strings.xmark)
    #
    #         result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #         if result.reaction.emoji == config_strings.checkmark:
    #             continue
    #         else:
    #             break
    #
    # @commands.command(name='changemywarstatus', pass_context=True,  brief='Change your war status')
    # @commands.has_role("has_war_permissions")
    # async def change_war_status(self, ctx):
    #     discord_id = ctx.message.author.id
    #
    #     # get accounts currently in clan
    #     accounts = clashAccessData.getLinkedAccountsList(
    #         discord_id, currently_in_clan_required=True)
    #
    #     if len(accounts) == 0:
    #         await discord_client.say('you must link accounts first!')
    #     else:
    #         question = 'Please hit the check on any accounts you want to add to war, and the x on any you want to remove from war.'
    #         await discord_client.say(question)
    #         for i in range(len(accounts)):
    #             account = accounts[i]
    #
    #             message = await discord_client.say('{}) {}\n'.format(i + 1, account))
    #
    #             async def wait_for_result(account, message, ctx):
    #
    #                 await discord_client.add_reaction(message, config_strings.checkmark)
    #                 await discord_client.add_reaction(message, config_strings.xmark)
    #
    #                 result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #                 if result.reaction.emoji == config_strings.checkmark:
    #                     result_string_temp = clashAccessData.addMemberToWar(
    #                         account)
    #                     if result_string_temp == config_strings.success:
    #                         result_string = '{} added to war'.format(account)
    #                     else:
    #                         result_string = 'Failed to add {} to war'.format(
    #                             account)
    #                 else:
    #                     result_string_temp = clashAccessData.removeMemberFromWar(
    #                         account)
    #                     if result_string_temp == config_strings.success:
    #                         result_string = '{} removed from war'.format(
    #                             account)
    #                     else:
    #                         result_string = 'Failed to remove {} from war'.format(
    #                             account)
    #                 await discord_client.send_message(ctx.message.channel, result_string)
    #
    #             discord_client.loop.create_task(wait_for_result(account, message, ctx))

    @commands.command(name='remindtoattack', pass_context=True,  brief='Remind members to attack!')
    @commands.has_role("coleaders")
    async def remind_members_to_attack_in_war(self, ctx):
        await discord_client.say("Reminders are being processed and will be sent momentarily!!")
        await send_out_war_reminders("")

    # use this right after asking for the member name
    async def get_member_instance_from_name_helper(self, ctx, database_accessor):

        message = await discord_client.wait_for_message(author=ctx.message.author)
        clash_account_name = message.content.upper()

        # get number of accounts matching this name
        member_instances = database_accessor.get_members_in_clan_with_name(clash_account_name)

        # if one, return it
        if len(member_instances) == 1:
            return member_instances[0]

        # if zero, say that this member couldn't be found, was it just added to the clan?
        # would need to refresh data and start process over again.
        if len(member_instances) == 0:
            raise MemberDoesNotExistException("This member could not be found. Was it added recently?")

        # if > 1 match, ask again with which TH the matches are
        # if both are the same TH, just use tags...
        matched_members = {}
        multiple_with_same_town_hall = False
        if len(member_instances) > 1:
            for member in member_instances:
                if member.town_hall_level in matched_members:
                    multiple_with_same_town_hall = True
                    break
                else:
                    matched_members[member.town_hall_level] = member

        if not multiple_with_same_town_hall:
            sorted_keys = sorted(matched_members, reverse=True)
            await discord_client.say("That name matched multiple accounts in the clan currently. Please select which you are looking for.")
            for key in sorted_keys:
                member = matched_members[key]
                message = await discord_client.say("Is it: {}, with TH {}?".format(member.member_name, member.town_hall_level))
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                if result.reaction.emoji == config_strings.checkmark:
                    return member
                else:
                    # keep looping
                    pass
            raise MemberNotSelectedException()
        else:
            await discord_client.say("That name matched multiple accounts in the clan currently. Please select which you are looking for.")
            for member in member_instances:
                message = await discord_client.say("Is it: {}, with member_tag {}?".format(member.member_name, member.member_tag))
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                if result.reaction.emoji == config_strings.checkmark:
                    return member
                else:
                    # keep looping
                    pass
            raise MemberNotSelectedException()

    async def set_cwl_roster_for_either_day(self, ctx, tomorrow_instead_of_today=False):

        # todo - verify that member doesn't already exist in CWL when adding
        # todo - save position on war map to print these in correct order...
        # todo - update DB to have access to what war day the current one is...

        await discord_client.say("Checking the current CWL war roster.")
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)

            modified = False

            try:
                if tomorrow_instead_of_today:
                    # get known members for current roster
                    current_roster_particips, war_instance = database_accessor.get_cwl_roster_and_war_tomorrow()
                else:
                    # get known members for current roster
                    current_roster_particips, war_instance = database_accessor.get_cwl_roster_and_war_today()
            except NoActiveClanWarLeagueWar:
                await discord_client.say("There is no active clan war league war.")
                return

            # print these, only an x or check under the second group
            known_members = []
            believed_members = []
            for war_particip in current_roster_particips:
                if war_particip.is_clan_war_league_war == 1:
                    # print("We know this member_instance is in for sure")
                    known_members.append(war_particip.member)
                elif war_particip.is_clan_war_league_war == 2:
                    # print("We have manually set this member_instance")
                    believed_members.append(war_particip.member)

            await discord_client.say("These members are definitely in war:")
            for member_instance in known_members:
                await discord_client.say(member_instance.member_name)
                await asyncio.sleep(1)
            if len(believed_members) > 0:
                await discord_client.say("These members are set as in war, but were manually set. They could be wrong. Please confirm them!")
                await discord_client.say("Hit the check on the members in the CWL, x on those not.")
                for member_instance in believed_members:
                    # print other details to be clear on duplicates? TH, hero levels, etc?
                    message = await discord_client.say(member_instance.member_name)
                    await discord_client.add_reaction(message, config_strings.checkmark)
                    await discord_client.add_reaction(message, config_strings.xmark)
                    result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                    if result.reaction.emoji == config_strings.checkmark:
                        continue
                    else:
                        # remove this member_instance
                        modified = True
                        database_accessor.remove_member_from_current_cwl(member_instance, war_instance)
                        await discord_client.say("Removed.")

            mems_in_war = len(known_members) + len(believed_members)
            await discord_client.say("This is a total of {} members in this CWL war.".format(mems_in_war))
            while True:
                message = await discord_client.say("Do you want to add someone else to this CWL?")
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                if result.reaction.emoji == config_strings.checkmark:
                    await discord_client.say("Who would you like to add?")
                    try:
                        member_instance = await self.get_member_instance_from_name_helper(ctx, database_accessor)
                        database_accessor.add_member_to_cwl(member_instance, war_instance)
                        modified = True
                        await discord_client.say("Added.")
                    except MemberDoesNotExistException as e:
                        await discord_client.say("This member doesn't seem to exist. Check if this account is in the clan currently.")
                        print(e)
                    except MemberNotSelectedException as e:
                        await discord_client.say("No member was selected. Check if this account is in the clan currently.")
                        print(e)
                else:
                    # we don't want to add anyone else
                    break

            if modified:
                if tomorrow_instead_of_today:
                    # get known members for current roster
                    current_roster_particips, war_instance = database_accessor.get_cwl_roster_and_war_tomorrow()
                else:
                    # get known members for current roster
                    current_roster_particips, war_instance = database_accessor.get_cwl_roster_and_war_today()

                # print these, only an x or check under the second group
                known_members = []
                believed_members = []
                for war_particip in current_roster_particips:
                    if war_particip.is_clan_war_league_war == 1:
                        # print("We know this member_instance is in for sure")
                        known_members.append(war_particip.member)
                    elif war_particip.is_clan_war_league_war == 2:
                        # print("We have manually set this member_instance")
                        believed_members.append(war_particip.member)

                await discord_client.say("Here's the updated roster.")
                await discord_client.say("These members are definitely in war:")
                for member_instance in known_members:
                    await discord_client.say(member_instance.member_name)
                    await asyncio.sleep(1)
                if len(believed_members) > 0:
                    await discord_client.say("These members are set as in war, but were manually set. They could be wrong. Please re run this command if you need to change them!")
                    for member_instance in believed_members:
                        # print other details to be clear on duplicates? TH, hero levels, etc?
                        await discord_client.say(member_instance.member_name)
                        await asyncio.sleep(1)
                await discord_client.say("This is a total of {} members in this CWL war.".format(len(current_roster_particips)))

    @commands.command(name='setnextcwlroster', pass_context=True,  brief='Set the CWL roster for the next day')
    @commands.has_role("developers")
    async def set_next_cwl_roster(self, ctx):
        await self.set_cwl_roster_for_either_day(ctx, tomorrow_instead_of_today=True)

    @commands.command(name='setcurrentcwlroster', pass_context=True,  brief='Set the CWL roster for the current day')
    @commands.has_role("developers")
    async def set_current_cwl_roster(self, ctx):
        await self.set_cwl_roster_for_either_day(ctx, tomorrow_instead_of_today=False)

class ClanGames:
    @commands.command(name='checkmyCGscores', pass_context=True,  brief='Check your recent Clan Games scores')
    @commands.has_role("developers")
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
            results = clashAccessData.getClanGamesResultsForMemberName(member_name)
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

    # @commands.command(name='checkineligibleforCG', pass_context=True,  brief='Get members that are too low TH for the CGs.')
    # @commands.has_role("developers")
    # async def getIneligibleTHs(self, ctx):
    #     roster = clashAccessData.getIneligibleForClanGames()
    #     await discord_client.say(roster)


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

        if time_since_filled > last_updated_data_time:
            time_checking = add_time_to_check()
            while last_updated_data_time < time_checking:
                await asyncio.sleep(1)

        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            result_string = database_accessor.get_all_donated_or_received_in_time_frame(time_since_created, time_since_filled)
        await discord_client.say(result_string)

    @commands.command(name='getallmemberswithoutdiscord', pass_context=True)
    @commands.has_role("coleaders")
    async def get_all_members_without_discord(self, ctx):
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            discord_id = ctx.message.author.id
            results = database_accessor.get_all_members_without_discord_as_string()
            await discord_client.say(results)

    @commands.command(name='getwarmemberswithoutdiscord', pass_context=True)
    @commands.has_role("developers")
    async def get_war_members_without_discord(self, ctx):
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            discord_id = ctx.message.author.id
            results = database_accessor.getMembersInWarWithoutDiscordAsString()
            await discord_client.say(results)

    # @commands.command(name='linkothersaccount', pass_context=True)
    # @commands.has_role("developers")
    # async def linkOthersAccounts(self, ctx, discordID, member_name):
    #     """Allows developer to provide a discord id and membername to link an account, should use linkmemberaccount instead"""
    #     member_name = member_name.upper()
    #     result = clashAccessData.link_discord_account(discordID, member_name, is_name=True)
    #     await discord_client.say(result)

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

    @commands.command(name='createdonationgraphs', pass_context=True)
    @commands.has_role("developers")
    async def create_donation_graphs(self, ctx):
        await discord_client.say('Working on it...')
        try:
            content_creator = ContentCreator()
            url = content_creator.generate_donation_webpage()
            await discord_client.say(url)
        except:
            await discord_client.say('An error occurred while generating the donation graphs.')

    # @commands.command(name='givememberwarpermissions', pass_context=True)
    # @commands.has_role("developers")
    # async def give_member_war_permissions(self, ctx):
    #     discordID = ctx.message.author.id
    #     await discord_client.say('Who would you like to set war permissions for?')
    #     message = await discord_client.wait_for_message(author=ctx.message.author)
    #     member_name = message.content.upper()
    #     account_exists = clashAccessData.verifyAccountExists(member_name)
    #     if account_exists:
    #         message = await discord_client.say('Should this account have permissions?')
    #         await discord_client.add_reaction(message, config_strings.checkmark)
    #         await discord_client.add_reaction(message, config_strings.xmark)
    #
    #         result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
    #         if result.reaction.emoji == config_strings.checkmark:
    #             count = clashAccessData.setWarPermissionVal(member_name, 1)
    #         else:
    #             count = clashAccessData.setWarPermissionVal(member_name, 0)
    #         await discord_client.say('{} rows changed.'.format(count))
    #         try:
    #             await update_roles()
    #             await discord_client.say("Applied roles")
    #         except:
    #             await discord_client.say("Failed to apply roles")
    #     else:
    #         await discord_client.say('Unable to find this account')


class TraderShop:

    @commands.command(name='sendtradernotifications', pass_context=True)
    @commands.has_role("developers")
    async def send_trader_notifications_command(self, ctx):
        await send_out_trader_reminders()

    @commands.command(name='setuptrader', pass_context=True)
    @commands.has_role("members")
    async def setup_trader(self, ctx):
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            trader_cycle_url = database_accessor.get_trader_cycle_url()
        intro_string = "As you likely know, the Trader sells items. Sometimes, these items are free, and sometimes they are considered a good value." \
            + " Before setting up your trader with ClashBot, please make sure you know what trader day your account is on! You can find it through this chart: {}".format(trader_cycle_url)
        await discord_client.say(intro_string)
        message = await discord_client.say("Do you know what trader day you are on?")
        await discord_client.add_reaction(message, config_strings.checkmark)
        await discord_client.add_reaction(message, config_strings.xmark)
        result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author, timeout=120)
        # if result is none, the bot didn't get a reaction in time
        if result is None:
            hit_check = (result.reaction.emoji == config_strings.checkmark)
            if hit_check:
                await self.set_trader_day(ctx)
                await discord_client.say("Be on the lookout for any reminders about free/high value items!")
                return
        await discord_client.say("Exiting. Please feel free to restart!")

    async def set_trader_day(self, ctx):
        discord_id = ctx.message.author.id
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            linked_member_accounts = database_accessor.get_linked_accounts(discord_id)
            await discord_client.say("Which account would you like to setup?")
            selected = False
            for member in linked_member_accounts:
                message = await discord_client.say(member.member_name)
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                hit_check = (result.reaction.emoji == config_strings.checkmark)
                if hit_check:
                    selected = True
                    trader_cycle_length = database_accessor.get_trader_cycle_length()
                    await discord_client.say('What trader cycle day is this account on? (Enter a number 1-{})'.format(trader_cycle_length))
                    message = await discord_client.wait_for_message(author=ctx.message.author)
                    try:
                        day_in_cycle = int(message.content)
                    except:
                        await discord_client.say("Failed to parse your input.")
                        return
                    try:
                        database_accessor.set_trader_day_for_member(member, day_in_cycle)
                    except TraderAccountNotConfigured:
                        await discord_client.say("This was not valid input.")
                        return
                    await discord_client.say("Trader day set!")
                    break
            if not selected:
                await discord_client.say("You didn't select an account to check")

    @commands.command(name='checkmytraderday', pass_context=True)
    @commands.has_role("members")
    async def get_trader_day(self, ctx):
        discord_id = ctx.message.author.id
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            results = database_accessor.get_linked_accounts(discord_id)
            await discord_client.say("Which account would you like to get it for?")
            selected = False
            for member in results:
                message = await discord_client.say(member.member_name)
                await discord_client.add_reaction(message, config_strings.checkmark)
                await discord_client.add_reaction(message, config_strings.xmark)
                result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
                hit_check = (result.reaction.emoji == config_strings.checkmark)
                if hit_check:
                    selected = True
                    try:
                        result = database_accessor.get_trader_day_for_member(member)
                    except TraderAccountNotConfigured:
                        await discord_client.say("This account hasn't been set up for the trader shop.")
                        return
                    await discord_client.say("This account is on day {} of the trader cycle.".format(result))
                    break
            if not selected:
                await discord_client.say("You didn't select an account to check")

    @commands.command(name='settradernotificationtime', pass_context=True)
    @commands.has_role("members")
    async def set_notification_time(self, ctx):
        discord_id = ctx.message.author.id
        dt = DateFetcherFormatter.get_utc_date_time()
        hour = dt.hour

        message = await discord_client.say("Is about now a good time for trader reminders? (Default is 12:30 AM UTC)")
        await discord_client.add_reaction(message, config_strings.checkmark)
        await discord_client.add_reaction(message, config_strings.xmark)
        result = await discord_client.wait_for_reaction([config_strings.checkmark, config_strings.xmark], message=message, user=ctx.message.author)
        hit_check = (result.reaction.emoji == config_strings.checkmark)
        if hit_check:
            with session_scope() as session:
                database_accessor = DatabaseAccessor(session)
                database_accessor.set_trader_time_for_discord_id(discord_id, hour)
            await discord_client.say("Done.")
        else:
            await discord_client.say("Ok, nevermind.")

    @commands.command(name='setitemsfornotification', pass_context=True)
    @commands.has_role("developers")
    async def set_items_for_notification(self, ctx):
        pass

    @commands.command(name='enablenotifications', pass_context=True)
    @commands.has_role("developers")
    async def enable_notifications(self, ctx):
        pass

    @commands.command(name='disablenotifications', pass_context=True)
    @commands.has_role("developers")
    async def disable_notifications(self, ctx):
        pass

    @commands.command(name='seetraderrotation', pass_context=True)
    @commands.has_role("members")
    async def see_trader_rotation(self, ctx):
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            trader_cycle_url = database_accessor.get_trader_cycle_url()
            await discord_client.say(trader_cycle_url)


trader_shop_cog = TraderShop()
discord_client.add_cog(trader_shop_cog)

clan_war_cog = ClanWar()
discord_client.add_cog(clan_war_cog)

clan_management_cog = ClanManagement()
discord_client.add_cog(clan_management_cog)

clan_games_cog = ClanGames()
discord_client.add_cog(clan_games_cog)

account_management_cog = AccountManagement()
discord_client.add_cog(account_management_cog)


async def update_roles():

    print('updating roles')
    with session_scope() as session:
        database_accessor = DatabaseAccessor(session)

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
        try:
            discord_ids_of_war_participants = database_accessor.get_discord_members_in_war()
        except NoActiveClanWar:
            discord_ids_of_war_participants = set()
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
                # @everyone is a role everyone has
                if len(server_member.roles) > 1:
                    await discord_client.remove_roles(server_member, member_role, war_role, troop_role, check_in_role, th12_role, war_perms_role)

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


async def send_out_trader_reminders():
    bot_channel = discord_client.get_channel(botChannelID)
    general_channel = discord_client.get_channel(generalChannelID)

    await discord_client.send_message(bot_channel, "Sending trader notifications")

    with session_scope() as session:
        database_accessor = DatabaseAccessor(session)
        results = database_accessor.get_accounts_who_get_trader_reminders(now_only=True)
        print(results)
        for discord_id, accounts_dict in results.items():
            discord_id = str(discord_id)
            member = server.get_member(discord_id)
            for account_name, items in accounts_dict.items():
                for item in items:
                    if member is None:
                        await discord_client.send_message(bot_channel, '{} would have gotten something, but seems to have left the server.'.format(account_name))
                    else:
                        await discord_client.send_message(general_channel, 'Hey {}, {} gets a {} today!'.format(member.mention, account_name, item))
                    await asyncio.sleep(1)

        results = database_accessor.get_accounts_who_get_trader_reminders(now_only=False)
        print(results)
        for discord_id, accounts_dict in results.items():
            discord_id = str(discord_id)
            member = server.get_member(discord_id)
            for account_name, items in accounts_dict.items():
                for item in items:
                    if member is None:
                        await discord_client.send_message(bot_channel, '{} would have gotten something, but seems to have left the server.'.format(account_name))
                    else:
                        await discord_client.send_message(bot_channel, 'Hey {}, {} gets a {} today!'.format(member.mention, account_name, item))
                    await asyncio.sleep(1)


async def trader_reminders_loop():

    # if the bot comes on before the half hour, send out these reminders, then start the loop
    current_time = DateFetcherFormatter.get_utc_date_time()
    next_time = current_time.replace(minute=30, second=0)
    if next_time > current_time:
        time_to_sleep = next_time - current_time
        print("1 sleeping for {}".format(time_to_sleep.total_seconds()))
        await asyncio.sleep(time_to_sleep.total_seconds())
        await send_out_trader_reminders()

    while True:

        current_time = DateFetcherFormatter.get_utc_date_time()
        print("2 current_time: {}".format(current_time))
        next_time = current_time + datetime.timedelta(hours=1)
        print("2 next_time a: {}".format(next_time))

        next_time = next_time.replace(minute=30, second=0)
        print("2 next_time b: {}".format(next_time))

        time_to_sleep = next_time - current_time
        print("2 time_to_sleep: {}".format(time_to_sleep.total_seconds()))

        # sleep for an hour
        await asyncio.sleep(time_to_sleep.total_seconds())

        # send out current reminders
        await send_out_trader_reminders()


async def send_out_war_reminders(next_war_timestamp_string):
    war_channel = discord_client.get_channel(warChannelID)
    bot_channel = discord_client.get_channel(testingChannelID)

    # update data to be sure we aren't sending reminders to people who have already attacked, just recently
    time_checking = add_time_to_check()
    while last_updated_data_time < time_checking:
        await asyncio.sleep(1)

    with session_scope() as session:
        database_accessor = DatabaseAccessor(session)
        try:
            accounts_that_need_to_attack = database_accessor.get_members_in_war_with_attacks_remaining()
        except NoActiveClanWar:
            await discord_client.say("There is no active clan war.")
            return
    for discord_id in accounts_that_need_to_attack["discord"]:
        account_names_dict = accounts_that_need_to_attack["discord"][discord_id]
        account_names_string = ""
        accounts_total = len(account_names_dict)
        current_account = 0
        for entry in account_names_dict:
            member_name = entry["member_name"]
            attacks_remaining = entry["attacks_remaining"]
            if attacks_remaining == 1:
                account_names_string += ' your {} attack with {}'.format(attacks_remaining, member_name)
            else:
                account_names_string += ' your {} attacks with {}'.format(attacks_remaining, member_name)
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
        if member is None:
            await discord_client.send_message(bot_channel, 'Hey someone is a bad sport and left during war. They had attacks remaining: {}'.format(account_names_string))
        else:
            await discord_client.send_message(war_channel, 'Hey {}, make sure to use{}! {}'.format(member.mention, account_names_string, next_war_timestamp_string))
        await asyncio.sleep(1)

async def war_reminders_loop():

    while True:
        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            next_timestamps_for_war = database_accessor.get_timestamps_for_current_war()
        if next_timestamps_for_war is None:
            await asyncio.sleep(3600*6)
        else:
            next_war_timestamp = next_timestamps_for_war[0][0]
            next_war_timestamp_string = next_timestamps_for_war[0][1]
            time_to_sleep = next_war_timestamp - DateFetcherFormatter.get_utc_timestamp()
            await asyncio.sleep(time_to_sleep)
            await send_out_war_reminders(next_war_timestamp_string)

async def createRules():
    rules_channel = discord_client.get_channel(rulesChannelID)
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

async def notify_if_cwl_roster_needs_set():
    war_channel = discord_client.get_channel(warChannelID)
    testing_channel = discord_client.get_channel(testingChannelID)
    with session_scope() as session:
        database_accessor = DatabaseAccessor(session)
        try:
            cwl_roster_complete = database_accessor.is_today_cwl_roster_complete()
        except NoActiveClanWarLeagueWar:
            return
        leader = server.get_member(leaderDiscordID)
        if not cwl_roster_complete:
            await discord_client.send_message(testing_channel, 'Hey {}, the CWL roster is NOT complete, please set it and then save data again so I can apply roles!!'.format(leader.mention))

async def discord_bot_data_loop():

    print('discord_bot_data_loop starting')

    global times_to_check_data
    # global last_updated_data
    global data_check_override

    global last_updated_data_time

    last_updated_data_time = FetchedDataProcessorHelper.last_processed_time_helper()

# self.previous_processed_time
#     last_updated_data = fetched_data_processor.previous_processed_time # clashAccessData.get_last_processed_time()

    # this is last retrieved, regardless of failure
    # last_fetched = clashAccessData.get_last_processed_time()

    # this handles startups, but prevents spammy startups when restarting several times in a row
    if DateFetcherFormatter.get_utc_timestamp() - last_updated_data_time > 60 * 60:
        data_check_override = True

    await discord_client.wait_until_ready()
    bot_channel = discord_client.get_channel(botChannelID)

    global server
    server = discord_client.get_server(server_id)

    discord_client.loop.create_task(trader_reminders_loop())
    discord_client.loop.create_task(war_reminders_loop())
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
            data_fetcher = SupercellDataFetcher()
            try:
                await discord_client.send_message(bot_channel, "Getting data")
                try:
                    await discord_client.loop.run_in_executor(None, data_fetcher.get_data_from_server)
                    await asyncio.sleep(1)
                except Exception as e:
                    await discord_client.send_message(bot_channel, "get_data_from_server: {}".format(e))
                    raise
                try:
                    data_valid = await discord_client.loop.run_in_executor(None, data_fetcher.validate_data)
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
                    data_valid = await discord_client.loop.run_in_executor(None, data_fetcher.validate_data)
                except:
                    await discord_client.send_message(bot_channel, "Something is not working")
                    data_valid = False
            if data_valid:
                await discord_client.send_message(bot_channel, "Data was retrieved")
                try:
                    last_updated_data_time = await discord_client.loop.run_in_executor(None, FetchedDataProcessorHelper.save_data_helper)
                    await asyncio.sleep(1)
                    await discord_client.send_message(bot_channel, "Data was saved")
                    try:
                        await update_roles()
                        await discord_client.send_message(bot_channel, "Applied roles")
                        try:
                            await notify_if_cwl_roster_needs_set()
                            await discord_client.send_message(bot_channel, "Notified that CWL roster needs set (if it does)")
                        except Exception:
                            await discord_client.send_message(bot_channel, "Failed to notify that CWL needs set")
                    except Exception:
                        await discord_client.send_message(bot_channel, "Failed to apply roles")
                except:
                    await discord_client.send_message(bot_channel, "Data failed to save")
            else:
                await discord_client.send_message(bot_channel, "Data was not retrieved")

    except Exception as err:
        print("Error: " + str(traceback.format_exc()))
        try:
            leader = server.get_member(leaderDiscordID)
            await discord_client.send_message(bot_channel, "Hey {}, an error occurred in ClashBot".format(leader.mention))
            await discord_client.send_message(bot_channel, str(traceback.format_exc()))
        except:
            print("Unable to send to discord.")


discord_client.loop.create_task(discord_bot_data_loop())

discord_client.run(token)
