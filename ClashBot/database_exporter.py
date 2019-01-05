from ClashBot import DatabaseAccessor, session_scope
from ClashBot.models import DISCORDACCOUNT, DISCORDCLASHLINK, MEMBER
import json

with session_scope() as session:
    database_accessor = DatabaseAccessor(session)

    resulting_data = {}

    # discord accounts
    discord_accounts = database_accessor.session.query(DISCORDACCOUNT).all()
    discord_property_list = []
    for discord_account_instance in discord_accounts:
        discord_property_dict = {
            'discord_id':  discord_account_instance.discord_tag,
            'is_donator':  discord_account_instance.is_troop_donator,
            'has_war_permissions':  discord_account_instance.has_permission_to_set_war_status,
            'time_last_checked_in':  discord_account_instance.time_last_checked_in,
            'trader_reminder_hour':  discord_account_instance.trader_shop_reminder_hour
        }
        discord_property_list.append(discord_property_dict)

    # discord clash links
    discord_name_list = []
    discord_clash_links = database_accessor.session.query(DISCORDCLASHLINK).all()
    for discord_clash_link_instance in discord_clash_links:
        discord_name_dict = {
            'discord_id':  discord_clash_link_instance.discord_tag,
            'member_tag':  discord_clash_link_instance.member_tag,
            'account_order':  discord_clash_link_instance.account_order
        }
        discord_name_list.append(discord_name_dict)

    resulting_data['DISCORD_PROPERTIES'] = discord_property_list
    resulting_data['DISCORD_NAMES'] = discord_name_list

    with open('exported_data/discord_exported_data.json', 'w') as outfile:
        json.dump(resulting_data, outfile, indent=4)

    member_data_to_export = []
    member_instances = database_accessor.session.query(MEMBER).all()
    for member_instance in member_instances:
        member_dict = {
            'member_tag':  member_instance.member_tag,
            'trader_rotation_offset':  member_instance.trader_rotation_offset
            # in the future, will add xbows, infernos, EA, etc
        }
        member_data_to_export.append(member_dict)

    with open('exported_data/member_data.json', 'w') as outfile:
        json.dump(member_data_to_export, outfile, indent=4)