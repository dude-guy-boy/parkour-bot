# errors.py

from interactions import Client, Extension, listen, Embed, events, CooldownSystem
from interactions.client.errors import CommandOnCooldown
from interactions.api.events.internal import CommandError, Error
import src.logs as logs
from datetime import timedelta
from lookups.colors import Color

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

    # @listen("on_command_error", disable_default_listeners=True)
    # async def on_cooldown_error(self, error: CommandError):
    #     # if isinstance(error, CommandOnCooldown):
    #     if hasattr(error, "cooldown"):
    #         cooldown: CooldownSystem = error.error.cooldown
    #         time = str(timedelta(seconds = round(cooldown.get_cooldown_time()))).split(":")
    #         hours = int(time[0])
    #         minutes = int(time[1])
    #         seconds = int(time[2])

    #         await error.ctx.send(embeds = Embed(description=f"You're on cooldown! Please wait `{str(hours) + ' hours' if hours > 0 else ''}{str(minutes) + ' minutes' if minutes > 0 else ''}{str(seconds) + ' seconds' if seconds > 0 else ''}`.", color=Color.RED))

    @listen("on_command_error", disable_default_listeners=True)
    async def on_cooldown_error(self, error: CommandError):
        try:
            cooldown: CooldownSystem = error.error.cooldown

            await error.ctx.send(embeds = Embed(description=f"You're on cooldown! Please wait `{round(cooldown.get_cooldown_time())}` seconds.", color=Color.RED))
        except:
            pass

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Errors(bot)