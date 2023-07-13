import re
from interactions import BaseChannel, Button, ButtonStyle, Client, BaseContext, ChannelType, Embed, GuildText, Member, Message, PermissionOverwrite, GuildChannel, TimestampStyles
from datetime import datetime
import emoji

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
    def make_message(self, message: Message, user_map: dict, replied_messages: dict, attachments_path: str):
        # TODO: Images, attachments, join messages when sent close together (this doesnt seem possible), more extensive markdown formatting, mention formatting
        # TODO: Replace in-content custom and default emojis and stickers
        
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
        components = ''
        slash_command = ''
        reactions = ''
        attachments = ''

        if message.components:
            components = self.make_components(message)

        if message.interaction:
            slash_command = self.make_slash_command(message, user_map)

        if message.reactions:
            reactions = self.make_reactions(message)

        if message.attachments:
            attachments = self.make_attachments(message, attachments_path)

        if message.sticker_items:
            print(message.sticker_items)

        return (header + slash_command + reply + embeds + components + reactions + attachments +
                f'{self.format_message_content(message.content)}\n'
                f'</discord-message>\n')

    @classmethod
    def make_attachments(self, message: Message, attachments_path: str):
        attachments_str = '<discord-attachments slot="attachments">\n'

        # TODO: Handle non media attachments

        for attachment in message.attachments:
            attachments_str += f'<discord-attachment url="{attachments_path}/{attachment.id}.{attachment.filename.split(".")[-1]}" alt="{attachment.filename}" width="850"></discord-attachment>\n'

        attachments_str += '</discord-attachments>\n'

        return attachments_str

    @classmethod
    def make_reactions(self, message: Message):
        emojis = []

        for reaction in message.reactions:
            if str(reaction.emoji).startswith("<:"):
                ext = ".gif" if reaction.emoji.animated else ".png"
                emoji_id = str(reaction.emoji).split(":")[2][:-1]

                # TODO: When interaction updates, change this url for emoji.url
                emojis.append((reaction.emoji.name, f"https://cdn.discordapp.com/emojis/{emoji_id}{ext}", reaction.count))
                break

            for emoji_item in emoji.emoji_list(str(reaction.emoji)):
                # Convert emoji unicode chars into twemoji image filename
                raw_emoji_unicode = emoji_item['emoji'].encode('unicode_escape').decode('utf-8')
                unicode_chars = raw_emoji_unicode.split('\\U000')[1:]
                emojis.append((emoji_item['emoji'], f"https://raw.githubusercontent.com/jdecked/twemoji/main/assets/svg/{'-'.join(unicode_chars)}.svg", reaction.count))

        reactions_str = '<discord-reactions slot="reactions">\n'
        for emoji_entry in emojis:
            reactions_str += f'<discord-reaction name="{emoji_entry[0]}" emoji="{emoji_entry[1]}" count="{emoji_entry[2]}"></discord-reaction>\n'

        reactions_str += '</discord-reactions>\n'

        return reactions_str

    @classmethod
    def make_slash_command(self, message: Message, user_map: dict):        
        return f'<discord-command slot="reply" profile="{user_map[int(message.interaction._user_id)]}" command="/{message.interaction.name}"></discord-command>'

    @classmethod
    def format_message_content(self, content: str):
        content = self.replace_multiline_code(content)
        content = self.replace_inline_code(content)

        content = self.replace_underline(content)

        content = self.replace_bold(content)
        content = self.replace_italics(content)

        content = self.replace_quote(content)

        content = self.replace_line_breaks(content)

        return content

    @classmethod
    def make_components(self, message: Message):
        rows = []

        for row in message.components:
            row_str = "<discord-action-row>\n"

            component: Button
            for component in row.components:
                if isinstance(component, Button):
                    # TODO: Link buttons
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
            embed_str += f'<discord-embed-description slot="description">{self.format_message_content(embed.description)}</discord-embed-description>\n'
            
            # Fields
            if embed.fields:
                embed_fields = '<discord-embed-fields slot="fields">\n'

                for field in embed.fields:
                    embed_fields += f'<discord-embed-field field-title="{field.name}">{self.format_message_content(field.value)}</discord-embed-field>\n'

                embed_fields += '</discord-embed-fields>\n'

                embed_str += embed_fields

            # Footer
            if embed.footer:
                footer_image = f'footer-image="{embed.footer.icon_url}"' if embed.footer.icon_url else ''
                footer_timestamp = ''

                if embed.timestamp:
                    footer_timestamp = 'timestamp="' + f"{embed.timestamp.day}/{embed.timestamp.month}/{embed.timestamp.year} {embed.timestamp.hour:02d}:{embed.timestamp.minute:02d}" + '"'

                embed_str += f'<discord-embed-footer slot="footer" {footer_image} {footer_timestamp}>{embed.footer.text}</discord-embed-footer>\n'

            embed_str += "</discord-embed>\n"
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

        return self.handy_replaces(template_content)
    
    @classmethod
    def replace_italics(self, text):
        return re.sub(r'([*_])(.*?)(?<!\\)\1', r'<discord-italic>\2</discord-italic>', text)
    
    @classmethod
    def replace_bold(self, text):
        return re.sub(r'\*\*(.*?)\*\*', r'<discord-bold>\1</discord-bold>', text)

    @classmethod
    def replace_quote(self, text):
        return re.sub(r'^> (.+?)(?:<br>)?$', r'<discord-quote>\1</discord-quote>', text, flags=re.MULTILINE)

    @classmethod
    def replace_multiline_code(self, text):
        return re.sub(r'```([^`]+)```', r'<code class="multiline">\1</code>', text)

    @classmethod
    def replace_inline_code(self, text):
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    @classmethod
    def replace_underline(self, text):
        return re.sub(r'__(.*?)__', r'<discord-underlined>\1</discord-underlined>', text)
    
    @classmethod
    def replace_line_breaks(self, text):
        return text.replace('\n', '<br>')
    
    @classmethod
    def handy_replaces(self, text: str):
        text = text.replace('<code class="multiline"><br>', '<code class="multiline">')
        text = text.replace('</discord-quote><br>', '</discord-quote>')

        return text