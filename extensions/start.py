# start.py

from interactions import Client, Extension, listen
import src.logs as logs

class Start(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @listen()
    async def on_startup(self):
        self.logger.info("Bot started!")

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Start(bot)