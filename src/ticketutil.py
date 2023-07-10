import re
from interactions import BaseChannel, Button, ButtonStyle, Client, BaseContext, ChannelType, Embed, GuildText, Member, Message, PermissionOverwrite, GuildChannel, TimestampStyles
from datetime import datetime

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
            
    @classmethod
    def is_ticket(self, channel: GuildChannel):
        return channel.type == ChannelType.GUILD_TEXT and channel.name.endswith("ticket")
    
    @classmethod
    def get_owner_id(self, channel: GuildText):
        try:
            return int(channel.topic.split(" | ")[0])
        except:
            return None
        
class Transcribe:

    @classmethod
    def make_profile(self, user: Member, ref_name: str):
        # format
        # skyra: {
        #     author: "Skyra",
        #     avatar: "https://github.com/NM-EEA-Y.png",
        #     roleColor: "#1e88e5",
        #     bot: true,
        # }

        # Get display colour
        display_colour = "#ffffff"

        for role in user.roles:
            if role.color.hex != "#000000":
                display_colour = role.color.hex
                break

        return (f'{ref_name}: {"{"}\n'
                f'author: "{user.display_name}",\n'
                f'avatar: "{user.avatar.url}",\n'
                f'roleColor: "{display_colour}",\n'
                f'bot: {str(user.bot).lower()}\n'
                '}')
    
    @classmethod
    def make_message(self, message: Message, user_map: dict, replied_messages: dict):
        # TODO: Images, attachments, reactions, join messages when sent close together, content markdown formatting, mention formatting
        
        reply = ""
        embeds = ""

        if message._referenced_message_id:
            reply = self.make_reply(replied_messages[int(message._referenced_message_id)], user_map[int(replied_messages[int(message._referenced_message_id)].author.id)]) + "\n"

        if message.embeds:
            embeds = self.make_embeds(message)

        time = f"{message.timestamp.day}/{message.timestamp.month}/{message.timestamp.year} {message.timestamp.hour:02d}:{message.timestamp.minute:02d}"

        header = f'<discord-message profile="{user_map[int(message.author.id)]}" timestamp="{time}"'

        if message.edited_timestamp:
            header += ' edited'

        header += '>\n'

        components = self.make_components(message)

        return (header + reply + embeds + components +
                f'  {self.format_message_content(message.content)}\n'
                f'</discord-message>\n')

    @classmethod
    def format_message_content(self, content: str):
        return content

    @classmethod
    def make_components(self, message: Message):
        rows = []

        for row in message.components:
            row_str = "<discord-action-row>\n"

            component: Button
            for component in row.components:
                if isinstance(component, Button):
                    print(component)
                    disabled = "disabled" if component.disabled else ""
                    row_str += f'<discord-button type="{self.button_type(int(component.style))}" {disabled}>{component.label}</discord-button>\n'
                
                # TODO: Handle select menus

            row_str += "</discord-action-row>"
            rows.append(row_str)

        return '<discord-attachments slot="components">\n' + "\n".join(rows) + '\n</discord-attachments>'

    @classmethod
    def button_type(self, number):
        match number:
            case 1:
                return "primary"
            case 2:
                return "secondary"
            case 3:
                return "success"
            case 4:
                return "destructive"

    @classmethod
    def make_embeds(self, message: Message):
        embeds = []

        embed: Embed
        for embed in message.embeds:
            author_image = f'author-image="{embed.author.icon_url}"' if embed.author else ''
            author_name = f'author-name="{embed.author.name}"' if embed.author else ''
            author_url = f'author-url="{embed.author.url}"' if embed.author else ''
            embed_color = f'color="#{hex(embed.color)[2:]}"' if embed.color else ''
            embed_title = f'embed-title="{embed.title}"' if embed.title else ''
            embed_image = f'image="{embed.image.url}"' if embed.image else ''
            embed_thumbnail = f'thumbnail="{embed.thumbnail.url}"' if embed.thumbnail else ''
            embed_url = f'url="{embed.url}"' if embed.url else ''

            embed_str = f'<discord-embed slot="embeds" {author_image} {author_name} {author_url} {embed_color} {embed_title} {embed_image} {embed_thumbnail} {embed_url}>\n'
            embed_str += f'<discord-embed-description slot="description">{embed.description}</discord-embed-description>\n'
            
            # Fields
            if embed.fields:
                embed_fields = '<discord-embed-fields slot="fields">\n'

                for field in embed.fields:
                    embed_fields += f'<discord-embed-field field-title="{field.name}">{field.value}</discord-embed-field>\n'

                embed_fields += '</discord-embed-fields>\n'

                embed_str += embed_fields

            # Footer
            if embed.footer:
                footer_image = f'footer-image="{embed.footer.icon_url}"' if embed.footer.icon_url else ''
                footer_timestamp = ''

                if embed.timestamp:
                    footer_timestamp = 'timestamp="' + f"{embed.timestamp.day}/{embed.timestamp.month}/{embed.timestamp.year} {embed.timestamp.hour:02d}:{embed.timestamp.minute:02d}" + '"'

                embed_str += f'<discord-embed-footer slot="footer" {footer_image} {footer_timestamp}>{embed.footer.text}</discord-embed-footer>\n'

            embed_str += "</discord-embed>"
            embeds.append(embed_str)

        return "\n".join(embeds)

    @classmethod
    def make_reply(self, message: Message, profile: str):
        # Check if replied message has attachment or has been edited
        # <discord-reply slot="reply" profile="skyra" edited attachment>What do you think about this image?</discord-reply>
        edited = "edited" if message.edited_timestamp else ""
        attachment = "attachment" if message.attachments or message.embeds else ""
        content = message.content if len(message.content) < 60 else message.content[:60] + "..."
        content = content if content else "<discord-italic>Click to see attachment</discord-italic>"

        return f'<discord-reply slot="reply" profile="{profile}" {edited} {attachment}>{content}</discord-reply>'

    @classmethod
    def make_transcript_html(self, owner_name: str, users: list, messages: list):
        # Grab template
        with open('./lookups/transcript_template.txt', 'r') as file:
            template_content = file.read()
        
        close_time = "10/10/10" #TODO: Get the start or end date for this
        users = ",\n".join(users)

        messages.reverse()
        messages = "".join(messages)

        template_content = template_content.replace("%%title%%", f"{owner_name}'s Ticket {close_time}")
        template_content = template_content.replace("%%profiles%%", users)
        template_content = template_content.replace("%%messages%%", messages)

        return template_content