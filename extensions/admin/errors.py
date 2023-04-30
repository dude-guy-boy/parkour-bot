# errors.py

from interactions import Client, Extension, listen
from interactions.api.events.internal import CommandError
import src.logs as logs

class Errors(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # TODO: Make this log traceback

    # @listen(disable_default_listeners=True)
    # async def on_command_error(self, error: CommandError):
    #     # cancel default interactions error msg
    #     # TODO: Make this configurable
    #     pass
        
def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Errors(bot)