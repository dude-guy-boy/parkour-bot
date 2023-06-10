# errors.py

import traceback
from interactions import EMBED_MAX_DESC_LENGTH, Client, Extension, listen, Embed, events, CooldownSystem
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

    @listen(disable_default_listeners=True)
    async def on_command_error(self, error: CommandError):
        # Handle cooldown error
        if await self.on_cooldown_error(error):
            return
        
        # Send traceback
        # TODO: In future make this send to the logging channel
        out = "".join(traceback.format_exception(error.error))
        await error.ctx.send(
            embeds=Embed(
                title=f"Error: {type(error.error).__name__}",
                color=Color.RED,
                description=f"```\n{out[:EMBED_MAX_DESC_LENGTH - 8]}```",
            )
        )

    async def on_cooldown_error(self, error: CommandError):
        try:
            cooldown: CooldownSystem = error.error.cooldown
            time = str(timedelta(seconds = round(cooldown.get_cooldown_time()))).split(":")
            hours = int(time[0])
            minutes = int(time[1])
            seconds = int(time[2])

            await error.ctx.send(embeds = Embed(description=f"You're on cooldown! Please wait `{self.format_cooldown(hours, minutes, seconds)}`.", color=Color.RED))
            return True
        except:
            return False

    def format_cooldown(self, hours, minutes, seconds):
        time_units = []
        if hours > 0:
            time_units.append(f"{hours} hour{'s' if hours > 1 else ''}")

        if minutes > 0:
            time_units.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

        if seconds > 0:
            time_units.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        if len(time_units) == 1:
            return time_units[0]

        if len(time_units) == 2:
            return f"{time_units[0]} and {time_units[1]}"

        return ', '.join(time_units[:-1]) + f" and {time_units[-1]}"

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Errors(bot)