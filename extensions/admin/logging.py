# logging.py

from interactions import (
    Client,
    Extension,
    listen,
    BaseContext,
    slash_command,
    SlashContext,
    slash_option,
    OptionType,
    GuildText,
    Embed
    )
from interactions.api.events.internal import CommandCompletion
from interactions.ext.prefixed_commands import PrefixedCommand
from interactions.ext.hybrid_commands.hybrid_slash import _HybridToPrefixedCommand
import src.logs as logs
from src.database import Config
from lookups.colors import Color

class Logging(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

        self.slash_logger = logs.init_logger("SLASH COMMAND")
        self.user_logger = logs.init_logger("USER COMMAND")
        self.msg_logger = logs.init_logger("MSG COMMAND")
        self.button_logger = logs.init_logger("BUTTON PRESS")
        self.menu_logger = logs.init_logger("SELECT MENU")
        self.modal_logger = logs.init_logger("MODAL SUBMIT")
        self.chat_logger = logs.init_logger("CHAT COMMAND")
        self.unknown_logger = logs.init_logger("UNKNOWN")

    def get_slash_command(self, ctx: BaseContext):
        # Handle if hybrid command
        if hasattr(ctx, "prefix"):
            self.process_prefixed_command(ctx)
            return

        command = "/" +ctx.__dict__['_command_name']

        # TODO: Handle discord option types like channel, user, etc
        # so that the command text displays them nicely

        for arg in ctx.__dict__['kwargs']:
            command += f" {arg}:{ctx.__dict__['kwargs'][arg]}"

        return command

    def process_prefixed_command(self, ctx: BaseContext):
        if "command" in ctx.__dict__:
            if type(ctx.__dict__["command"]) == PrefixedCommand or _HybridToPrefixedCommand:
                command = ctx.message.content
                self.chat_logger.info(f"{ctx.user.username}#{ctx.user.discriminator} performed the prefixed command '{command}' in #{ctx.channel.name}")
                return True
        return False

    @listen()
    async def on_command_completion(self, event: CommandCompletion):

        # Process if prefixed command
        if self.process_prefixed_command(event.ctx):
            return

        # TODO: Add funcs to process other command types

        # Process as slash command
        command = self.get_slash_command(event.ctx)
        self.slash_logger.info(f"{event.ctx.user.username}#{event.ctx.user.discriminator} performed the command '{command}' in #{event.ctx.channel.name}")

    ### /CONFIG LOGGING SET-CHANNEL ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="logging",
        group_description="group logging config command",
        sub_cmd_name="set-channel",
        sub_cmd_description="Set the channel that logs will be sent in"
    )
    @slash_option(
        name="channel",
        description="The channel you would like to set",
        required=True,
        opt_type=OptionType.CHANNEL
    )
    async def config_log_channel(self, ctx: SlashContext, channel: GuildText):
        Config.set_config_parameter(key="channel_id", value= str(channel.id))
        await ctx.send(embed=Embed(description=f"Set logging channel to <#{channel.id}>", color=Color.GREEN))

    # TODO: Add command to send log through discord

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Logging(bot)