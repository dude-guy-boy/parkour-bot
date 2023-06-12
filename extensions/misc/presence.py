# activity.py

from interactions import (
    Client,
    Extension,
    SlashCommand,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    Activity,
    ActivityType
    )
import src.logs as logs
from lookups.colors import Color

class Presence(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # Base bot command
    activity = SlashCommand(name="activity", description="base activity command")

    ### /ACTIVITY SET PLAYING text ###
    @activity.subcommand(
        group_name="set",
        group_description="activity set group",
        sub_cmd_name="playing",
        sub_cmd_description="Shows bot as playing something"
    )
    @slash_option(
        name="text",
        description="Playing <text>",
        required=True,
        opt_type=OptionType.STRING
    )
    async def activity_playing(self, ctx: SlashContext, text: str):
        await self.bot.change_presence(activity=Activity(name=text, type=ActivityType.PLAYING))
        await ctx.send(embed=Embed(description=f"Set the bot presence/activity to: `Playing {text}`", color=Color.GREEN), ephemeral=True)

    ### /ACTIVITY SET WATCHING text ###
    @activity.subcommand(
        group_name="set",
        group_description="activity set group",
        sub_cmd_name="watching",
        sub_cmd_description="Shows bot as watching something"
    )
    @slash_option(
        name="text",
        description="Watching <text>",
        required=True,
        opt_type=OptionType.STRING
    )
    async def activity_watching(self, ctx: SlashContext, text: str):
        await self.bot.change_presence(activity=Activity(name=text, type=ActivityType.WATCHING))
        await ctx.send(embed=Embed(description=f"Set the bot presence/activity to: `Watching {text}`", color=Color.GREEN), ephemeral=True)

    ### /ACTIVITY SET LISTENING-TO text ###
    @activity.subcommand(
        group_name="set",
        group_description="activity set group",
        sub_cmd_name="listening-to",
        sub_cmd_description="Shows bot as listening to something"
    )
    @slash_option(
        name="text",
        description="Listening to <text>",
        required=True,
        opt_type=OptionType.STRING
    )
    async def activity_listening(self, ctx: SlashContext, text: str):
        await self.bot.change_presence(activity=Activity(name=text, type=ActivityType.LISTENING))
        await ctx.send(embed=Embed(description=f"Set the bot presence/activity to: `Listening to {text}`", color=Color.GREEN), ephemeral=True)

    ### /ACTIVITY SET COMPETING-IN text ###
    @activity.subcommand(
        group_name="set",
        group_description="activity set group",
        sub_cmd_name="competing-in",
        sub_cmd_description="Shows bot as competing in something"
    )
    @slash_option(
        name="text",
        description="Competing in <text>",
        required=True,
        opt_type=OptionType.STRING
    )
    async def activity_competing(self, ctx: SlashContext, text: str):
        await self.bot.change_presence(activity=Activity(name=text, type=ActivityType.COMPETING))
        await ctx.send(embed=Embed(description=f"Set the bot presence/activity to: `Competing in {text}`", color=Color.GREEN), ephemeral=True)

    ### /ACTIVITY SET STREAMING text ###
    @activity.subcommand(
        group_name="set",
        group_description="activity set group",
        sub_cmd_name="streaming",
        sub_cmd_description="Shows bot as streaming. Text is what the bot is playing"
    )
    @slash_option(
        name="text",
        description="Streaming <text>",
        required=True,
        opt_type=OptionType.STRING
    )
    async def activity_streaming(self, ctx: SlashContext, text: str):
        await self.bot.change_presence(activity=Activity(name=text, type=ActivityType.STREAMING))
        await ctx.send(embed=Embed(description=f"Set the bot presence/activity to: `Streaming` and `Playing {text}`", color=Color.GREEN), ephemeral=True)

    ### /ACTIVITY CLEAR ###
    @activity.subcommand(
        sub_cmd_name="clear",
        sub_cmd_description="Clears the bots activity"
    )
    async def activity_competing(self, ctx: SlashContext):
        await self.bot.change_presence(activity=None)
        await ctx.send(embed=Embed(description=f"Cleared the bot presence/activity", color=Color.GREEN), ephemeral=True)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Presence(bot)