# logging.py

from interactions import Client, Extension, listen, BaseContext
from interactions.api.events.internal import CommandCompletion
import src.logs as logs

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

        for arg in ctx.__dict__['kwargs']:
            command += f" {arg}:{ctx.__dict__['kwargs'][arg]}"

        return command

    @listen()
    async def on_command_completion(self, event: CommandCompletion):
        command = self.get_command(event.ctx)
        self.slash_logger.info(command)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Logging(bot)