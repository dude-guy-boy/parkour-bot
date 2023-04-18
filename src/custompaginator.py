from interactions.ext import paginators as standard_paginator
from interactions.ext.paginators import Page
from interactions.ext.paginators import Timeout
from interactions.client.utils.serializer import export_converter
from interactions import (
    ActionRow,
    Button,
    ButtonStyle,
    Client,
    MISSING,
    BaseContext,
    Message,
    PartialEmoji,
    SlashContext,
    TYPE_ALL_CHANNEL,
    ComponentContext,
    StringSelectMenu,
    StringSelectOption,
    process_emoji,
    spread_to_rows
    )
import textwrap, asyncio, attrs
from typing import List, Optional, Union

@attrs.define(eq=False, order=False, hash=False, kw_only=False)
class Paginator(standard_paginator.Paginator):

    allow_multi_user: bool = attrs.field(repr=False, default=True)
    '''Allows multiple users to use this paginator'''

    first_button_label: str = "<<"
    '''Sets the first page button label'''

    back_button_label: str = "<"
    '''Sets the previous page button label'''

    next_button_label: str = ">"
    '''Sets the next page button label'''

    last_button_label: str = ">>"
    '''Sets the last page button label'''

    @classmethod
    def create_from_string(
        cls,
        client: "Client",
        content: str,
        prefix: str = "",
        suffix: str = "",
        num_lines: int = MISSING,
        page_size: int = 4000,
        timeout: int = 0,
        allow_multi_user: bool = False
    ) -> "standard_paginator.Paginator":
        """
        Create a paginator from a list of strings. Useful to maintain formatting.
        Can also use a set line number which is useful for lists / leaderboards

        Args:
            client: A reference to the client
            content: The content to paginate
            prefix: The prefix for each page to use
            suffix: The suffix for each page to use
            num_lines: The maximum number of lines for each page
            page_size: The maximum number of characters for each page
            timeout: A timeout to wait before closing the paginator

        Returns:
            A paginator system
        """

        # If num_lines not set, don't split pages by line
        if num_lines == MISSING:
            content_pages = textwrap.wrap(
                content,
                width=page_size - (len(prefix) + len(suffix)),
                break_long_words=True,
                break_on_hyphens=False,
                replace_whitespace=False,
            )
            pages = [standard_paginator.Page(c, prefix=prefix, suffix=suffix) for c in content_pages]
            return cls(client, pages=pages, timeout_interval=timeout, allow_multi_user=allow_multi_user)
        
        else:
            num_lines = max(1, num_lines) # Make sure number of lines is at least one
            page_size = max(1, page_size) # Make sure max page length is at least one

            page_lists = cls.__break_lines(cls, lines = content.split("\n"), num_lines = num_lines, page_size = page_size)

            pages = []

            for page in page_lists:
                pages.append(standard_paginator.Page(content="\n".join(page), prefix=prefix, suffix=suffix))

            return cls(client, pages=pages, timeout_interval=timeout, allow_multi_user=allow_multi_user)
    
    def __break_lines(self, lines, num_lines, page_size):
        result = []
        page = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # Add 1 for the newline character

            # If theres more room on this page, and the line
            # won't cause the page to exceed the max length
            if len(page) < num_lines and current_length + line_length <= page_size:
                page.append(line)
                current_length += line_length

            # If theres more room on the page, but the
            # line is longer than a half page
            elif len(page) < num_lines and line_length > page_size / 2:
                # Fill rest of page with the line
                first, remaining = self.__break_string(self, input_str = line, max_len = (page_size - sum(len(s) for s in page)))
                page.append(first)
                result.append(page)

                # Continue next page with the rest of the line
                page = [remaining]
                current_length = len(remaining)

            # If theres no room left on the page or adding the line would
            # cause the page to exceed its max length
            else:
                result.append(page)
                page = [line]
                current_length = line_length

        result.append(page)
        
        return result
    
    async def send(self, ctx: Optional[Union[BaseContext, SlashContext]] = None, channel_id: Optional[int] = None, ephemeral: bool = False, author_id: Optional[int] = None) -> Message:
        """
        Send this paginator. Modified to allow ephemeral sending and sending to a specific channel

        Args:
            ctx: The context to send this paginator with
            channel: The channel to send this paginator to
            author: The paginator author ()
            ephemeral: Whether the paginator should be sent ephemerally or not

        Returns:
            The resulting message

        """

        if (channel_id and ctx) or (not channel_id and not ctx):
            raise ValueError('You must input either ctx or the target channel')
        
        if channel_id and not self.allow_multi_user and not author_id:
            raise ValueError("You must specify the author_id to send paginator to a channel when allow_multi_user is False")

        if channel_id:
            channel: TYPE_ALL_CHANNEL = await self.client.fetch_channel(channel_id=channel_id)
            self._message = await channel.send(**self.to_dict())
            self._author_id = None if self.allow_multi_user else author_id

        elif(ctx):
            if(type(ctx) == SlashContext):
                self._message = await ctx.send(**self.to_dict(), ephemeral=ephemeral)
            else:
                self._message = await ctx.send(**self.to_dict())
        
            self._author_id = ctx.author.id

        if self.timeout_interval > 1:
            self._timeout_task = Timeout(self)
            _ = asyncio.create_task(self._timeout_task())

        return self._message

    def create_components(self, disable: bool = False) -> List[ActionRow]:
        """
        Create the components for the paginator message.

        Args:
            disable: Should all the components be disabled?

        Returns:
            A list of ActionRows

        """
        output = []

        if self.show_select_menu:
            current = self.pages[self.page_index]
            output.append(
                StringSelectMenu(
                    *(
                        StringSelectOption(
                            label=f"{i+1} {p.get_summary if isinstance(p, Page) else p.title}", value=str(i)
                        )
                        for i, p in enumerate(self.pages)
                    ),
                    custom_id=f"{self._uuid}|select",
                    placeholder=f"{self.page_index+1} {current.get_summary if isinstance(current, Page) else current.title}",
                    max_values=1,
                    disabled=disable,
                )
            )

        if self.show_first_button:
            output.append(
                Button(
                    style=self.default_button_color,
                    custom_id=f"{self._uuid}|first",
                    disabled=disable or self.page_index == 0,
                    label = self.first_button_label
                )
            )
        if self.show_back_button:
            output.append(
                Button(
                    style=self.default_button_color,
                    custom_id=f"{self._uuid}|back",
                    disabled=disable or self.page_index == 0,
                    label = self.back_button_label
                )
            )

        if self.show_callback_button:
            output.append(
                Button(
                    style=self.default_button_color,
                    emoji=PartialEmoji.from_dict(process_emoji(self.callback_button_emoji)),
                    custom_id=f"{self._uuid}|callback",
                    disabled=disable,
                )
            )

        if self.show_next_button:
            output.append(
                Button(
                    style=self.default_button_color,
                    custom_id=f"{self._uuid}|next",
                    disabled=disable or self.page_index >= len(self.pages) - 1,
                    label = self.next_button_label
                )
            )
        if self.show_last_button:
            output.append(
                Button(
                    style=self.default_button_color,
                    custom_id=f"{self._uuid}|last",
                    disabled=disable or self.page_index >= len(self.pages) - 1,
                    label = self.last_button_label
                )
            )

        return spread_to_rows(*output)

    async def _on_button(self, ctx: ComponentContext, *args, **kwargs) -> Optional[Message]:
        '''
        Handles paginator button presses
        Modified to allow multiple users to use the paginator if set
        '''

        if (ctx.author.id != self.author_id) and not self.allow_multi_user:
            return (
                await ctx.send(self.wrong_user_message, ephemeral=True)
                if self.wrong_user_message
                else await ctx.defer(edit_origin=True)
            )
        
        if self._timeout_task:
            self._timeout_task.ping.set()
        match ctx.custom_id.split("|")[1]:
            case "first":
                self.page_index = 0
            case "last":
                self.page_index = len(self.pages) - 1
            case "next":
                if (self.page_index + 1) < len(self.pages):
                    self.page_index += 1
            case "back":
                if self.page_index >= 1:
                    self.page_index -= 1
            case "select":
                self.page_index = int(ctx.values[0])
            case "callback":
                if self.callback:
                    return await self.callback(ctx)

        await ctx.edit_origin(**self.to_dict())
        return None

    def __break_string(self, input_str, max_len):
        words = input_str.split()
        output_str = ''
        for word in words:
            if len(output_str + ' ' + word) > max_len:
                break
            else:
                output_str += ' ' + word
        remaining_str = input_str[len(output_str):]
        return output_str.strip(), remaining_str.strip()