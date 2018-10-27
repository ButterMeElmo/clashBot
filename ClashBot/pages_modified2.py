import asyncio
import discord


class CannotPaginate(Exception):
    pass


class Pages:
    """Implements a paginator that queries the user for the
    pagination interface.
    Pages are 1-index based, not 0-index based.
    If the user does not reply within 2 minutes, the pagination
    interface exits automatically.
    """

    def __init__(self, bot, *, message, category_dict, per_page=9):
        self.bot = bot
        self.category_dict = category_dict
        self.message = message
        self.author = message.author
        self.per_page = per_page
        self.total_entries = 0
        pages = 0
        for category_name, category_entries in category_dict.items():
            self.total_entries += len(category_entries)
            pages_for_category, left_over = divmod(
                len(category_entries), self.per_page)
            pages += pages_for_category
            if left_over:
                pages += 1
        self.maximum_pages = pages
        self.embed = discord.Embed()
        self.paginating = pages > 1
        self.reaction_emojis = [
            #            ('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.first_page),
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
            #            ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.last_page),
            #            ('\N{INPUT SYMBOL FOR NUMBERS}', self.numbered_page ),
            #            ('\N{BLACK SQUARE FOR STOP}', self.stop_pages),
            #            ('\N{INFORMATION SOURCE}', self.show_help),
        ]

        server = self.message.server
        if server is not None:
            self.permissions = self.message.channel.permissions_for(server.me)
        else:
            self.permissions = self.message.channel.permissions_for(
                self.bot.user)

        if not self.permissions.embed_links:
            raise CannotPaginate('Bot does not have embed links permission.')

    def get_page(self, page):
        print('looking for page {}'.format(page))
        current_page_checked = 0
        for category_name, category_entries in self.category_dict.items():
            print(category_name)
            print(category_entries)
            # if this category has multiple pages
            if (len(category_entries) > self.per_page):

                # find the maximum page number that this category holds
                number_of_pages_in_category, remainder = divmod(
                    len(category_entries), self.per_page)
                if remainder:
                    number_of_pages_in_category += 1

                # check to see if we want this page
                for i in range(0, number_of_pages_in_category):
                    if (current_page_checked + i) == page:
                        start = i*self.per_page
                        commands_from_category_on_this_page = category_entries[start:(
                            start + self.per_page)]
                        command_names = []
                        for command_name, command in commands_from_category_on_this_page:
                            command_names.append(command_name)
                        return category_name, command_names
                current_page_checked += number_of_pages_in_category

            # if this category only has one page
            else:
                # if this page is the one we want, return it
                if (current_page_checked + 1) == page:
                    command_names = []
                    for command_name, command in category_entries:
                        command_names.append(command_name)
                    return category_name, command_names

                current_page_checked += 1

        print('I shouldn\'t get here')

    async def show_page(self, page, *, first=False):
        self.current_page = page
        category_name, entries = self.get_page(page)
        p = []
        p.append(category_name)
        for t in enumerate(entries, 1):
            p.append('%s. %s' % t)

        self.embed.set_footer(text='Page %s/%s (%s entries)' %
                              (page, self.maximum_pages, self.total_entries))

        if not self.paginating:
            self.embed.description = '\n'.join(p)
            return await self.bot.send_message(self.message.channel, embed=self.embed)

        if not first:
            self.embed.description = '\n'.join(p)
            await self.bot.edit_message(self.message, embed=self.embed)
            return

        # verify we can actually use the pagination session
        if not self.permissions.add_reactions:
            raise CannotPaginate('Bot does not have add reactions permission.')

        if not self.permissions.read_message_history:
            raise CannotPaginate(
                'Bot does not have Read Message History permission.')

#        p.append('')
#        p.append('Confused? React with \N{INFORMATION SOURCE} for more info.')
        self.embed.description = '\n'.join(p)
        self.message = await self.bot.send_message(self.message.channel, embed=self.embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 2 and reaction in ('\u23ed', '\u23ee'):
                # no |<< or >>| buttons if we only have two pages
                # we can't forbid it if someone ends up using it but remove
                # it from the default set
                continue
            try:
                await self.bot.add_reaction(self.message, reaction)
            except discord.NotFound:
                # If the message isn't found, we don't care about clearing anything
                return

    async def checked_show_page(self, page):
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self):
        """goes to the first page"""
        await self.show_page(1)

    async def last_page(self):
        """goes to the last page"""
        await self.show_page(self.maximum_pages)

    async def next_page(self):
        """goes to the next page"""
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self):
        """goes to the previous page"""
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self):
        if self.paginating:
            await self.show_page(self.current_page)

    async def numbered_page(self):
        """lets you type a page number to go to"""
        to_delete = []
        to_delete.append(await self.bot.send_message(self.message.channel, 'What page do you want to go to?'))
        msg = await self.bot.wait_for_message(author=self.author, channel=self.message.channel,
                                              check=lambda m: m.content.isdigit(), timeout=30.0)
        if msg is not None:
            page = int(msg.content)
            to_delete.append(msg)
            if page != 0 and page <= self.maximum_pages:
                await self.show_page(page)
            else:
                to_delete.append(await self.bot.say('Invalid page given. (%s/%s)' % (page, self.maximum_pages)))
                await asyncio.sleep(5)
        else:
            to_delete.append(await self.bot.send_message(self.message.channel, 'Took too long.'))
            await asyncio.sleep(5)

        try:
            await self.bot.delete_messages(to_delete)
        except Exception:
            pass

    async def show_help(self):
        """shows this message"""
        e = discord.Embed()
        messages = ['Welcome to the interactive paginator!\n']
        messages.append('This interactively allows you to see pages of text by navigating with '
                        'reactions. They are as follows:\n')

        for (emoji, func) in self.reaction_emojis:
            messages.append('%s %s' % (emoji, func.__doc__))

        e.description = '\n'.join(messages)
        e.colour = 0x738bd7  # blurple
        e.set_footer(text='We were on page %s before this message.' %
                     self.current_page)
        await self.bot.edit_message(self.message, embed=e)

        async def go_back_to_current_page():
            await asyncio.sleep(60.0)
            await self.show_current_page()

        self.bot.loop.create_task(go_back_to_current_page())

    async def stop_pages(self):
        """stops the interactive pagination session"""
        await self.bot.delete_message(self.message)
        self.paginating = False

    def react_check(self, reaction, user):
        if user is None or user.id != self.author.id:
            return False

        for (emoji, func) in self.reaction_emojis:
            if reaction.emoji == emoji:
                self.match = func
                return True
        return False

    async def paginate(self, start_page=1):
        """Actually paginate the entries and run the interactive loop if necessary."""
        await self.show_page(start_page, first=True)

        while self.paginating:
            react = await self.bot.wait_for_reaction(message=self.message, check=self.react_check, timeout=120.0)
            if react is None:
                self.paginating = False
                try:
                    await self.bot.clear_reactions(self.message)
                except:
                    pass
                finally:
                    break

            try:
                await self.bot.remove_reaction(self.message, react.reaction.emoji, react.user)
            except:
                pass  # can't remove it so don't bother doing so

            await self.match()
