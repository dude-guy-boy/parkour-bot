# times.py

from interactions import (
    Client,
    Extension,
    Member,
    SlashCommand,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Config, UserData
import pytz
from datetime import datetime

class Times(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### Time base command ###
    time = SlashCommand(name="time", description="base bot command")

    ### /TIME ZONE timezone ###
    @time.subcommand(
        sub_cmd_name="zone",
        sub_cmd_description="Get the current time in any timezone"
    )
    @slash_option(
        name="timezone",
        description="The timezone you want the time of",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
    )
    async def time_zone(self, ctx: SlashContext, timezone: str):
        tz = pytz.timezone(timezone)
        place_now = datetime.now(tz)
        formatted_time = place_now.strftime("%I:%M %p, %B %d")
        await ctx.send(embeds = Embed(description = f"In `{timezone}` it is currently `{formatted_time}`", color=Color.GREEN))

    ### /TIME SET-MY-ZONE timezone ###
    @time.subcommand(
        sub_cmd_name="set-my-zone",
        sub_cmd_description="Set your own timezone. NOTE: This will not be revealed to other users when checking"
    )
    @slash_option(
        name="timezone",
        description="The timezone you want to set as your",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
    )
    async def time_set_my_zone(self, ctx: SlashContext, timezone: str):
        UserData.set_user(str(ctx.author.id), data={"timezone": timezone})

        await ctx.send(embeds=Embed(description=f"Set your timezone to `{timezone}`!", color=Color.GREEN), ephemeral=True)
        
        await logs.DiscordLogger.log(self.bot, ctx, f"{ctx.author.mention} set their timezone")
        self.logger.info(f"{ctx.author.user.username} set their timezone")

    ### /TIME USER user ###
    @time.subcommand(
    sub_cmd_name="user",
    sub_cmd_description="Get the time for another user"
    )
    @slash_option(
        name="user",
        description="The user you want to get the time of",
        opt_type=OptionType.USER,
        required=True
    )
    async def time_user(self, ctx: SlashContext, user: Member):
        data = UserData.get_user(str(user.id))

        if not data:
            await ctx.send(embed=Embed(description=f"{user.mention} hasn't set their timezone!", color=Color.RED))
            return
        
        timezone = data['timezone']
        tz = pytz.timezone(timezone)
        place_now = datetime.now(tz)
        formatted_time = place_now.strftime("%I:%M %p, %B %d")
        await ctx.send(embeds = Embed(description = f"For {user.user.mention} it is currently `{formatted_time}`", color=Color.GREEN))

    ### Timezone autocomplete ###
    @time_zone.autocomplete("timezone")
    @time_set_my_zone.autocomplete("timezone")
    async def timezone_autocomplete(self, ctx: AutocompleteContext):
        choices = []

        for zone in pytz.all_timezones:
            zone_time = datetime.now(pytz.timezone(zone))
            choices.append({"name": f"{zone} UTC{zone_time.strftime('%z')}", "value": zone})

        filtered_choices = []
        for choice in choices:
            if ctx.input_text.lower() in choice['name'].lower():
                filtered_choices.append(choice)

        await ctx.send(filtered_choices[:25])

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Times(bot)