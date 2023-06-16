# polls.py

from interactions import (
    Attachment,
    Client,
    EmbedAttachment,
    Extension,
    File,
    Guild,
    Role,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    Button,
    ButtonStyle,
    AutocompleteContext,
    GuildChannel,
    SlashCommandChoice
    )
import requests
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data
import re, emoji

class Polls(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # TODO: Add emoji-polls, sticker-polls
    # Polls that ask to add / remove an emoji or sticker

    ### /POLL ###
    @slash_command(
        name="poll",
        description="Just a template command",
    )
    @slash_option(
        name="question",
        description="Enter your poll question here",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="emojis",
        description="Enter your poll emojis here",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="image",
        description="Upload an image for your poll",
        required=False,
        opt_type=OptionType.ATTACHMENT
    )
    @slash_option(
        name="anonymous",
        description="Do you want your poll to be anonymous?",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Yes", value="Yes"),
            SlashCommandChoice(name="No", value="")
        ]
    )
    @slash_option(
        name="thread",
        description="Do you want your poll to have an attached thread?",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Yes", value="Yes"),
            SlashCommandChoice(name="No", value="")
        ]
    )
    async def poll_command(self, ctx: SlashContext, question: str, emojis: str = None, image: Attachment = None, anonymous: bool = False, thread: bool = False):
        await ctx.defer(ephemeral=True)
        
        # Set default emojis if custom emojis werent specified
        if not emojis:
            emojis = "⬆️ ⬇️ ↕️"

        # Make sure question isn't empty / has words
        if not self.check_valid_question(question):
            await ctx.send(embeds=Embed(description=f"Invalid question: `{question}`.", color=Color.RED))
            return
        
        # Check if inaccessible or duplicate emojis were entered
        emoji_list = self.get_emojis(emojis)
        emoji_list, duplicates = self.check_duplicate_emojis(emoji_list)
        emoji_list, inaccessible = await self.check_accessible_emojis(ctx.guild, emoji_list)

        # If too few emojis entered
        if len(emoji_list) <= 1:
            await ctx.send(embeds=Embed(title="Too Few Emojis Entered", description=f"You entered `{len(emoji_list)}` unique emojis: `{', '.join(emoji_list)}`. To use custom emojis, you need to specify at least two unique emojis.", color=Color.RED))
            return

        # If an inaccessible emoji was entered
        if inaccessible:
            valid_emojis = "- " + "\n- ".join(emoji_list)

            await ctx.send(embeds=Embed(title="Inaccessible Emojis Entered", description=f"Unable to access the following emojis: '{' '.join(inaccessible)}'.", color=Color.RED))
            return

        # If duplicate emojis were entered
        if duplicates:
            valid_emojis = "- " + "\n- ".join(emoji_list)

            embed = Embed(title="Duplicate Emojis Entered",
                description=f"You entered '{' '.join(duplicates)}' multiple times! Would you like to send the poll anyway with the following emojis?\n{valid_emojis}", color=Color.YORANGE)
            
            buttons = [
                Button(style=ButtonStyle.SUCCESS, label="Send Anyway", custom_id=f"send_poll_anyway"),
                Button(style=ButtonStyle.DANGER, label="Don't Send", custom_id=f"dont_send_poll")
            ]

            duplicate_send_anyway_message = await ctx.send(embed = embed, components=buttons, ephemeral=True)

            response = await self.bot.wait_for_component(
                messages=duplicate_send_anyway_message,
                components=buttons
            )

            # Don't send the poll
            if response.ctx.custom_id == "dont_send_poll":
                buttons[0].disabled = True
                buttons[1].disabled = True
                await response.ctx.edit_origin(embeds=Embed(description="Your poll has been cancelled", color=Color.GREEN), components=buttons)
                return
            
            # Send the poll
            buttons[0].disabled = True
            buttons[1].disabled = True
            await response.ctx.edit_origin(embeds=Embed(description="OK! sending your poll...", color=Color.GREEN), components=buttons)

        # Get the poll number
        try:
            poll_number = Data.get_data_item("poll_number")
        except:
            poll_number = 1

        # Create the poll embed
        embed = Embed(title = f"Poll #{poll_number}", description = question, color = Color.GREEN)

        # Set poll author
        if anonymous:
            embed.set_author(
                name=f"Anonymous User", icon_url="https://cdn.discordapp.com/attachments/972473507223056384/986914030130188308/2123041_copy.png")
        else:
            embed.set_author(
                name=f"{ctx.member.user.display_name}", icon_url=ctx.member.user.avatar.url)

        # Set image if needed
        file = None
        if image:
            response = requests.get(image.url, stream=True)
            with open(f"./images/poll_{image.filename}", 'wb') as f:
                f.write(response.content)

            file = File(f"./images/poll_{image.filename}")
            embed.image = EmbedAttachment(url=f"attachment://poll_{image.filename}")

        # Get the poll channel
        polls_channel_id = Config.get_config_parameter("poll_channel_id")
        if not polls_channel_id:
            await ctx.send(embeds=Embed(description="The poll channel could not be found :sob:. Please notify a staff member", color=Color.RED))
            return

        # Send the poll
        polls_channel = await ctx.guild.fetch_channel(polls_channel_id)
        poll = await polls_channel.send(embed = embed, file=file)

        # Increment poll number
        poll_number += 1
        Data.set_data_item("poll_number", poll_number)

        # Add poll reactions
        for emoji in emoji_list:

            # If custom emoji, remove the '<>' so it can be used
            if emoji.startswith("<"):
                emoji = emoji[1:len(emoji)-1]

            await poll.add_reaction(emoji)

        # Create poll thread if specified
        if thread:
            thread_title = f"Poll Discussion - {question}"
            if len(thread_title) > 100:
                thread_title = thread_title[:97] + "..."

            await polls_channel.create_thread(name=thread_title, auto_archive_duration=1440, message=poll, reason="Poll thread")

        # Respond to the user
        await ctx.send(embeds=Embed(description="Successfully sent your poll!", color=Color.GREEN), ephemeral=True)

        # Log anonymous polls
        # TODO: Improve logging
        if anonymous:
            await logs.DiscordLogger.log_raw(self.bot, f"{ctx.author.mention} created an anonymous poll: `{question}`, Thread: {thread}, Emojis: {', '.join(emoji_list)}")
        else:
            await logs.DiscordLogger.log_raw(self.bot,f"{ctx.author.mention} created a poll: `{question}`, Thread: {thread}, Emojis: {', '.join(emoji_list)}")

        self.logger.info(f"{ctx.author.user.username}#{ctx.author.user.discriminator} created a poll: '{question}', Anonymous: {anonymous}, Thread: {thread}, Emojis: {emoji_list}")

    # Checks if the input emojis are accessible by the bot
    async def check_accessible_emojis(self, guild: Guild, emoji_list):
        guild_emojis = await guild.fetch_all_custom_emojis()
        guild_emoji_list = []
        accessible_emoji_list = []
        inaccessible_emoji_list = []

        for emoji in guild_emojis:
            guild_emoji_list.append(f"<:{emoji.name}:{emoji.id}>")

        for emoji in emoji_list:
            if not emoji.startswith("<"):
                accessible_emoji_list.append(emoji)
                continue

            if emoji in guild_emoji_list:
                accessible_emoji_list.append(emoji)
            else:
                inaccessible_emoji_list.append(emoji)                

        return accessible_emoji_list, inaccessible_emoji_list

    # Checks if the input emojis contain any duplicates
    def check_duplicate_emojis(self, emoji_list):
        refined_emoji_list = list(set(emoji_list))
        duplicate_emojis = [emoji for emoji in emoji_list if emoji_list.count(emoji) > 1]
        
        return refined_emoji_list, duplicate_emojis

    def get_emojis(self, emoji_string):
        # Extract unicode and custom emojis from the string
        emoji_list = emoji.emoji_list(emoji_string)
        emoji_list += self.custom_emoji_list(emoji_string)

        # Reconstruct emoji order to match the original string
        emoji_list = sorted(emoji_list, key=lambda x: x['match_start'])

        return [emoji['emoji'] for emoji in emoji_list]

    def custom_emoji_list(self, emoji_string):
        emoji_list = []
        emoji_start = None
        
        for idx, char in enumerate(emoji_string):
            if char == "<":
                emoji_start = idx
            elif char == ">" and emoji_start is not None:
                emoji_list.append({"match_start": emoji_start, "emoji": emoji_string[emoji_start:idx + 1]})
                emoji_start = None
        
        return emoji_list

    def check_valid_question(self, question):
        return not re.match(r'^[_\W]+$', question)

    ### /CONFIG POLLS SET-CHANNEL ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="polls",
        group_description="polls group command",
        sub_cmd_name="set-channel",
        sub_cmd_description="Set the channel that polls should be sent to"
    )
    @slash_option(
        name="channel",
        description="The channel polls will be sent to",
        opt_type=OptionType.CHANNEL,
        required=True
    )
    async def config_polls_set_channel(self, ctx: SlashContext, channel: GuildChannel):
        Config.set_config_parameter("poll_channel_id", str(channel.id))
        await ctx.send(embed=Embed(description=f"Successfully set the poll channel to {channel.mention}", color=Color.GREEN), ephemeral=True)

     ### /CONFIG POLLS SET-POLLNT ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="polls",
        group_description="polls group command",
        sub_cmd_name="set-pollnt",
        sub_cmd_description="Set the role that makes users unable to make polls"
    )
    @slash_option(
        name="role",
        description="The role that makes users unable to make polls",
        opt_type=OptionType.ROLE,
        required=True
    )
    async def config_polls_set_pollnt(self, ctx: SlashContext, role: Role):
        Config.set_config_parameter("pollnt_role_id", str(role.id))
        await ctx.send(embed=Embed(description=f"Successfully set the polln't role to {role.mention}", color=Color.GREEN), ephemeral=True)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Polls(bot)