# -*- coding: utf-8 -*-

import pages_modified2
from discord.ext.commands import HelpFormatter, Paginator, Command
import inspect
import itertools
import asyncio
import re


class MyHelpFormatter(HelpFormatter):

    def _add_subcommands_to_page(self, max_width, commands, mobile_format):
        for name, command in commands:
            if name in command.aliases:
                # skip aliases
                continue
            if mobile_format:
                entry = '  {0}'.format(name)
            else:
                entry = '  {0:<{width}} {1}'.format(
                    name, command.short_doc, width=max_width)
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)

    def format_help_for(self, context, command_or_bot, mobileFormat):
        self.context = context
        self.command = command_or_bot
        return self.format(mobileFormat)

    def format(self, mobileFormat):
        """Handles the actual behaviour involved with formatting.
        To change the behaviour, this method should be overridden.
        Returns
        --------
        list
                        A paginated output of the help command.
        """
        self._paginator = Paginator()

        # we need a padding of ~80 or so

        description = self.command.description if not self.is_cog(
        ) else inspect.getdoc(self.command)

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):
            # <signature portion>
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)
            elif self.command.brief:
                self._paginator.add_line(self.command.brief, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'

        if self.is_bot():
            data = sorted(self.filter_command_list(), key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = list(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(
                    max_width, commands, mobileFormat)
        else:
            self._paginator.add_line('Commands:')
            self._add_subcommands_to_page(
                max_width, self.filter_command_list(), mobileFormat)

        if not mobileFormat:
            # add the ending note
            self._paginator.add_line()
            ending_note = self.get_ending_note()
            self._paginator.add_line(ending_note)
        return self._paginator.pages


_mentions_transforms = {
    '@everyone': '@\u200beveryone',
    '@here': '@\u200bhere'
}

_mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))


@asyncio.coroutine
def _default_help_command(ctx, *commands: str):
    """Shows this message."""
    bot = ctx.bot
    destination = ctx.message.author if bot.pm_help else ctx.message.channel

    def repl(obj):
        return _mentions_transforms.get(obj.group(0), '')

    mobileFormat = False
    # help by itself just lists our own commands.
    if len(commands) == 0:
        mobileFormat = True
        pages = bot.formatter.format_help_for(ctx, bot, mobileFormat)
    elif len(commands) == 1 and commands[0].upper() == 'BETA':

        category_dict = {}

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'
        bot.formatter.context = ctx
        bot.formatter.command = bot
        all_commands_temp = sorted(
            bot.formatter.filter_command_list(), key=category)
        for category_temp, commands_temp in itertools.groupby(all_commands_temp, key=category):
            commands_temp = list(commands_temp)
            if len(commands_temp) > 0:
                category_dict[category_temp] = commands_temp
        mypages = pages_modified2.Pages(
            bot, message=ctx.message, category_dict=category_dict)
        yield from mypages.paginate()
        return
    elif len(commands) == 1 and commands[0].upper() == 'LONG':
        pages = bot.formatter.format_help_for(ctx, bot, mobileFormat)
    elif len(commands) == 1 and commands[0].upper() == 'COLEADERS':
        mobileFormat = True
        origRoles = ctx.message.author.roles[:]
        for role in ctx.message.author.roles:
            if role.name == 'developers':
                ctx.message.author.roles.remove(role)
        pages = bot.formatter.format_help_for(ctx, bot, mobileFormat)
        origRoles = ctx.message.author.roles = origRoles
    elif len(commands) == 1 and commands[0].upper() == 'MEMBERS':
        mobileFormat = True
        origRoles = ctx.message.author.roles[:]
        matched_roles = []
        for role in ctx.message.author.roles:
            if role.name == 'developers':
                matched_roles.append(role)
            elif role.name == 'coleaders':
                matched_roles.append(role)
        for role in matched_roles:
            ctx.message.author.roles.remove(role)
        pages = bot.formatter.format_help_for(ctx, bot, mobileFormat)
        origRoles = ctx.message.author.roles = origRoles
    elif len(commands) == 1:
        # try to see if it is a cog name
        name = _mention_pattern.sub(repl, commands[0])
        command = None
        if name in bot.cogs:
            command = bot.cogs[name]
        else:
            command = bot.commands.get(name)
            if command is None:
                yield from bot.send_message(destination, bot.command_not_found.format(name))
                return

        pages = bot.formatter.format_help_for(ctx, command, mobileFormat)
    else:
        name = _mention_pattern.sub(repl, commands[0])
        command = bot.commands.get(name)
        if command is None:
            yield from bot.send_message(destination, bot.command_not_found.format(name))
            return

        for key in commands[1:]:
            try:
                key = _mention_pattern.sub(repl, key)
                command = command.commands.get(key)
                if command is None:
                    yield from bot.send_message(destination, bot.command_not_found.format(key))
                    return
            except AttributeError:
                yield from bot.send_message(destination, bot.command_has_no_subcommands.format(command, key))
                return

        pages = bot.formatter.format_help_for(ctx, command, mobileFormat)

    if bot.pm_help is None:
        characters = sum(map(lambda l: len(l), pages))
        # modify destination based on length of pages.
        if characters > 1000:
            destination = ctx.message.author

    for page in pages:
        yield from bot.send_message(destination, page)
