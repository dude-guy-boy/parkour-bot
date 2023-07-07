from interactions import BaseChannel, Client, BaseContext, ChannelType, GuildText, Member, PermissionOverwrite, GuildChannel

class Ticket:
    @classmethod
    async def create(cls, ctx: BaseContext, name: str, overwrites: list[PermissionOverwrite], category: int, identifier: str):
        channel = await ctx.guild.create_channel(channel_type = ChannelType.GUILD_TEXT, name = name, topic = identifier, category = category, overwrites = overwrites)
        return channel
    
    @classmethod
    async def fetch_ticket(self, ctx: BaseContext, ticket_identifier, category_id) -> GuildText:
        channels: list[BaseChannel] = await ctx.guild.fetch_channels()

        for channel in channels:
            if channel.type == ChannelType.GUILD_TEXT and channel.parent_id == category_id and channel.topic == ticket_identifier:
                return channel