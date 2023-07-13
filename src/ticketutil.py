import os
import re
from interactions import BaseChannel, Button, ButtonStyle, Client, BaseContext, ChannelType, Embed, GuildText, Member, Message, PermissionOverwrite, GuildChannel, StickerFormatType, StickerItem, TimestampStyles
import emoji
from PIL import Image
from moviepy.editor import VideoFileClip
import imageio
from src.download import download

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
    async def make_message(self, message: Message, user_map: dict, replied_messages: dict, attachments_path: str, roles, channels, users):
        # TODO: connect messages when sent close together
        
        reply = ""
        embeds = ""

        if message._referenced_message_id:
            reply = self().make_reply(replied_messages[int(message._referenced_message_id)], user_map[int(replied_messages[int(message._referenced_message_id)].author.id)]) + "\n"

        if message.embeds:
            embeds = self().make_embeds(message, roles, channels, users)

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
            components = self().make_components(message)

        if message.interaction:
            slash_command = self().make_slash_command(message, user_map)

        if message.reactions:
            reactions = self().make_reactions(message)

        if message.attachments or message.sticker_items:
            attachments = await self().make_attachments(message, attachments_path)

        return (header + slash_command + reply + embeds + components + reactions + attachments +
                f'{self().format_message_content(message.content, roles, channels, users)}\n'
                f'</discord-message>\n')

    async def make_attachments(self, message: Message, attachments_path: str):
        attachments_str = '<discord-attachments slot="attachments">\n'

        # Send stickers as attachments
        if message.sticker_items:
            attachments_str += await self.make_stickers(message, attachments_path)

        # Figure out attachment type
        if message.attachments:
            for attachment in message.attachments:
                attachment_filepath = f'{attachments_path}/{attachment.id}.{attachment.filename.split(".")[-1]}'

                # Figure out type
                file_ext = attachment.filename.split(".")[-1]
                if file_ext.lower() in ("jpg", "jpeg", "png", "gif", "gifv"):
                    attachments_str += self.make_image_attachment(attachment_filepath)
                    continue

                if file_ext.lower() in ("webm", "mp4", "mov"):
                    attachments_str += self.make_video_attachment(attachment_filepath, file_ext)
                    continue

                if file_ext.lower() in ("mp3", "wav", "ogg", "flac"):
                    attachments_str += self.make_audio_attachment(attachment_filepath, attachment.filename, file_ext)
                    continue

                attachments_str += self.make_non_embed_attachment(attachment_filepath, attachment.filename, file_ext)

        attachments_str += '</discord-attachments>\n'

        return attachments_str

    async def make_stickers(self, message: Message, attachments_path: str):
        stickers_str = ''

        for sticker in message.sticker_items:
            # If its a LOTTIE sticker
            if sticker.format_type == StickerFormatType.LOTTIE:
                sticker_path = f"{attachments_path}/{sticker.id}.json"

                if f'{sticker.id}.json' not in os.listdir(attachments_path):
                    await download(f"https://cdn.discordapp.com/stickers/{sticker.id}.json", sticker_path)

                stickers_str += (
                    f'<div id="lottie-container-{sticker.id}" style="width: 160px;"></div>\n'
                    '<script>\n'
                    "    var animation = bodymovin.loadAnimation({\n"
                    f"        container: document.getElementById('lottie-container-{sticker.id}'),\n"
                    f"        path: '{sticker_path}',\n"
                    "        renderer: 'svg',\n"
                    "        loop: true,\n"
                    "        autoplay: true,\n"
                    "        name: 'sticker'\n"
                    "    })\n"
                    '</script>\n'
                )

                continue
            
            # If its a normal sticker
            if f'{sticker.id}.png' not in os.listdir(attachments_path):
                sticker_url = f"https://cdn.discordapp.com/stickers/{sticker.id}.png"
                stickers_str += f'<discord-attachment url="{sticker_url}" alt="{sticker.id}.png" width="160"></discord-attachment>\n'

        return stickers_str

    def make_image_attachment(self, filepath: str):
        width = self.get_media_width(filepath)
        return f'<discord-attachment url="{filepath}" alt="{filepath.split("/")[-1]}" width="{width}"></discord-attachment>\n'

    def make_non_embed_attachment(self, filepath: str, filename: str, file_ext: str):
        return (
            '<div style="width: 500px; padding: 10px; box-sizing: border-box; border-radius: 10px; background-color: #2f3136; text-indent: 5px; border: 0.5px solid #282828;">\n'
            '<div>\n'
            '<img src="assets/emptydoc.svg" width="30px" style="float: left; padding-top: 0px; padding-right: 5px; padding-left: 5px;" alt="file">\n'
            f'<p style="margin-top: 5px; margin-bottom: 0px; padding-bottom: 0px; font-size: 18px;"><a href="{filepath}" download>{filename}</a></p>\n'
            f'<p style="margin-top: -5px; margin-bottom: 5px; padding-top: 0px; font-size: 12px; color: #868484; font-weight: 500;">{self.get_file_size(filepath)}</p>\n'
            '</div></div>\n'
        )

    def make_audio_attachment(self, filepath: str, filename: str, file_ext: str):
        return (
            '<div style="width: 500px; padding: 10px; box-sizing: border-box; border-radius: 10px; background-color: #2f3136; text-indent: 5px; border: 0.5px solid #282828;">\n'
            '<div><img src="assets/audiodoc.svg" width="24px" style="float: left; padding-top: 4px; padding-right: 5px; padding-left: 5px;" alt="audio">\n'
            f'<p style="margin-top: 0px; margin-bottom: 0px; padding-bottom: 0px; font-size: 18px;"><a href="{filepath}" download>{filename}</a></p>\n'
            f'<p style="margin-top: -5px; margin-bottom: 8px; padding-top: 0px; font-size: 12px; color: #868484; font-weight: 500;">{self.get_file_size(filepath)}</p></div>\n'
            f'<audio controls style="width: 450px;"><source src="{filepath}" type="audio/{file_ext}">Your browser does not support the audio element.</audio></div>\n'
        )

    def make_video_attachment(self, filepath: str, file_ext: str):
        width = self.get_media_width(filepath)
        return f'<video width="{width}" controls><source src="{filepath}" type="video/{file_ext}">Your browser does not support the video tag.</video>\n'

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

    def make_slash_command(self, message: Message, user_map: dict):        
        return f'<discord-command slot="reply" profile="{user_map[int(message.interaction._user_id)]}" command="/{message.interaction.name}"></discord-command>'

    def format_message_content(self, content: str, roles, channels, users):
        # TODO: Role, user and channel mentions

        # TODO: Add markdown headings
        # TODO: Replace in-content custom and default emojis

        content = self.replace_multiline_code(content)
        content = self.replace_inline_code(content)

        content = self.replace_underline(content)

        content = self.replace_bold(content)
        content = self.replace_italics(content)

        content = self.replace_quote(content)

        content = self.replace_line_breaks(content)

        content = self.format_channel_mentions(content, channels)
        content = self.format_user_mentions(content, users)
        content = self.format_role_mentions(content, roles)

        return content

    def format_emojis(self, text):
        pass

    def format_user_mentions(self, text: str, users: dict):
        for user in users:
            text = text.replace(f"<@{user}>", f"<discord-mention>{users[user]}</discord-mention>")

        return text
    
    def format_role_mentions(self, text: str, roles: dict):
        for role in roles:
            text = text.replace(f"<@&{role}>", f'<discord-mention type="role" color="{roles[role][1]}">{roles[role][0]}</discord-mention>')

        return text
    
    def format_channel_mentions(self, text: str, channels: dict):
        for channel in channels:
            text = text.replace(f"<#{channel}>", f'<discord-mention type="channel">{channels[channel]}</discord-mention>')

        return text

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

    def make_embeds(self, message: Message, roles, channels, users):
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
            embed_str += f'<discord-embed-description slot="description">{self.format_message_content(embed.description, roles, channels, users)}</discord-embed-description>\n'
            
            # Fields
            if embed.fields:
                embed_fields = '<discord-embed-fields slot="fields">\n'

                for field in embed.fields:
                    embed_fields += f'<discord-embed-field field-title="{field.name}">{self.format_message_content(field.value, roles, channels, users)}</discord-embed-field>\n'

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

        return self().handy_replaces(template_content)
    
    def replace_italics(self, text):
        return re.sub(r'([*_])(.*?)(?<!\\)\1', r'<discord-italic>\2</discord-italic>', text)
    
    def replace_bold(self, text):
        return re.sub(r'\*\*(.*?)\*\*', r'<discord-bold>\1</discord-bold>', text)

    def replace_quote(self, text):
        return re.sub(r'^> (.+?)(?:<br>)?$', r'<discord-quote>\1</discord-quote>', text, flags=re.MULTILINE)

    def replace_multiline_code(self, text):
        return re.sub(r'```([^`]+)```', r'<code class="multiline">\1</code>', text)

    def replace_inline_code(self, text):
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    def replace_underline(self, text):
        return re.sub(r'__(.*?)__', r'<discord-underlined>\1</discord-underlined>', text)
    
    def replace_line_breaks(self, text):
        return text.replace('\n', '<br>')
    
    def handy_replaces(self, text: str):
        text = text.replace('<code class="multiline"><br>', '<code class="multiline">')
        text = text.replace('</discord-quote><br>', '</discord-quote>')

        return text
    
    def get_media_width(self, media_path):
        default_width = 850
        
        try:
            if media_path.lower().endswith((".png", ".jpg", ".jpeg")):
                with Image.open(media_path) as image:
                    width = image.size[0]
            elif media_path.lower().endswith((".gif", ".apng")):
                with imageio.imread(media_path) as gif:
                    width = gif.shape[1]
            elif media_path.lower().endswith((".mp4", ".webm")):
                clip = VideoFileClip(media_path)
                width = clip.size[0]
                clip.close()
            else:
                return default_width
            
            return min(default_width, width)
        except Exception as e:
            return default_width
        
    def get_file_size(self, filepath):
        if os.path.exists(filepath):
            file_size_in_bytes = os.path.getsize(filepath)
            return self.convert_file_size(file_size_in_bytes)
        
        return "???"
    
    def convert_file_size(self, size_in_bytes):
        if size_in_bytes < 0:
            raise ValueError("Size must be a non-negative number.")

        suffixes = ['bytes', 'KB', 'MB', 'GB']
        suffix_index = 0

        while size_in_bytes >= 1024 and suffix_index < len(suffixes) - 1:
            size_in_bytes /= 1024
            suffix_index += 1

        if suffix_index == 0:
            return f"{int(size_in_bytes)} {suffixes[suffix_index]}"
        else:
            return f"{size_in_bytes:.2f} {suffixes[suffix_index]}"