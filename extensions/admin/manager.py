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

class Manager(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @slash_command(
        name="bot",
        description="base bot command",
        sub_cmd_name="restart",
        sub_cmd_description="Restarts the bot"
    )
    async def bot_restart(self, ctx: SlashContext):
        # Set channel where message should be sent on startup
        Data.set_data_item("restart_channel", str(ctx.channel.id))
        await ctx.send(embeds=Embed(description="Restarting...", color=Color.YORANGE))
        self.logger.info("Restarting bot & socket server")

        # Kill server process so it will also be restarted
        server_process_id = Data.get_data_item("server_process_id")
        kill(server_process_id, SIGKILL)

        # Restarts bot
        execl(executable, *([executable]+argv))

    # TODO: Add management commands
    # Bot restart
    # Bot reload
    # Bot update
    # Force backup
    # Get backup
    # Get logs

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Manager(bot)