from interactions import Embed, InteractionContext, Message
from lookups.colors import Color

async def send(ctx: InteractionContext, content: str, color: int = Color.GREEN, ephemeral: bool = False, to_channel: bool = False):
    if to_channel:
        return await ctx.channel.send(embed=Embed(description=content, color=color))
    
    return await ctx.send(embed=Embed(description=content, color=color), ephemeral=ephemeral)

async def edit(message: Message, content: str, color: int = Color.GREEN):
    return await message.edit(embed=Embed(description=content, color=color))