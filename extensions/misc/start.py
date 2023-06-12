# start.py

from interactions import Client, Extension, listen, Embed
from src.database import Data
from lookups.colors import Color
import src.logs as logs

class Start(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @listen()
    async def on_startup(self):
        # Check if bot was restarted
        try:
            if channel_id := Data.get_data_item("restart_channel", name="manager"):
                Data.delete_item({"key": "restart_channel", "value": channel_id}, name="manager")

                channel = self.bot.get_channel(channel_id)
                await channel.send(embed=Embed(description="Restarted!", color=Color.GREEN))
                
                self.logger.info("Bot restarted!")
        except:
            self.logger.info("Bot started!")

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Start(bot)