# errors.py

from interactions import Client, Extension, listen
import interactions.api.events.internal
import src.logs as logs

class Errors(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @listen(disable_default_listeners=True)
    async def on_command_error(self, error: interactions.api.events.internal.CommandError):
        pass
        
def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Errors(bot)