# manager.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data
from os import execl, kill
from sys import executable, argv
from signal import SIGKILL
from git import Repo

class Manager(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()
        self.repo = Repo('.')
        assert not self.repo.bare

    # TODO: Add management commands
    # Force backup
    # Get backup
    # Get logs

    ### /BOT RESTART ###
    @slash_command(
        name="bot",
        description="base bot command",
        sub_cmd_name="restart",
        sub_cmd_description="Restarts the bot"
    )
    async def bot_restart(self, ctx: SlashContext):
        await self.restart(ctx)

    ### /BOT UPDATE ###
    @slash_command(
        name="bot",
        description="base bot command",
        sub_cmd_name="update",
        sub_cmd_description="Updates the bot"
    )
    async def bot_update(self, ctx: SlashContext):
        await ctx.defer()

        try:
            # Do the pull
            git = self.repo.git
            pull = git.pull()

            # Format the pull
            split_string = pull.split('\n')
            formatted_string = ''
            for line in split_string:
                line = line.lstrip()
                formatted_string = f"{formatted_string}\n> {line}"

            # Send updates
            await ctx.send(embeds=Embed(description=f"**Pulling Repository:**{formatted_string}", color=Color.GREEN))

            # Log the update
            # TODO: discord logger
            # await self.discord_logger.log_command(ctx, f"Pulled repository.{formatted_string}")
            reformatted = formatted_string.replace('\n', ':')
            self.logger.info(f"Pulled repository. {reformatted}")
            await self.restart(ctx)
        except:
            await ctx.send(embeds=Embed(description="Failed to pull updates", color=Color.RED))
            self.logger.warning("Failed to pull repository")
            await self.discord_logger.log_command(ctx, f"Failed to pull repository")

    async def restart(self, ctx: SlashContext):
        # Set channel where message should be sent on startup
        Data.set_data_item("restart_channel", str(ctx.channel.id))
        await ctx.send(embeds=Embed(description="Restarting...", color=Color.YORANGE))
        self.logger.info("Restarting bot & socket server")

        # Kill server process so it will also be restarted
        server_process_id = Data.get_data_item("server_process_id")
        kill(server_process_id, SIGKILL)

        # Restarts bot
        execl(executable, *([executable]+argv))

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Manager(bot)