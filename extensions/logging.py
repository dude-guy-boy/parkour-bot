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
import src.logs as logs
from src.database import Config

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

    def get_command(self, ctx: BaseContext):
        command = "/" +ctx.__dict__['_command_name']

        # TODO: Handle discord option types like channel, user, etc
        # so that the command text displays them nicely

        for arg in ctx.__dict__['kwargs']:
            command += f" {arg}:{ctx.__dict__['kwargs'][arg]}"

        return command

    @listen()
    async def on_command_completion(self, event: CommandCompletion):
        command = self.get_command(event.ctx)
        self.slash_logger.info(command)

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
        Config.set_config_parameter({"channel_id": str(channel.id)})
        await ctx.send(embed=Embed())

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Logging(bot)