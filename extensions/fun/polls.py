# polls.py

from collections import OrderedDict
import os
from interactions import (
    Attachment,
    Client,
    EmbedAttachment,
    EmbedAuthor,
    Extension,
    File,
    Guild,
    Member,
    Role,
    SlashCommand,
    listen,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    Button,
    ButtonStyle,
    GuildChannel,
    SlashCommandChoice,
    Task,
    IntervalTrigger
    )
from interactions.api.events.discord import MessageDelete
import requests
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data
import re, emoji
from src.files import File as BotFile
from datetime import datetime, timedelta

class Polls(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()
        self.emoji_add_poll_finish.start()
        self.emoji_remove_poll_finish.start()

    # TODO: Add sticker-polls

    ### /EMOJI-POLL ###
    emoji_poll = SlashCommand(name="emoji-poll", description="base emoji-poll command")

    ### /EMOJI-POLL REMOVE-EMOJI ###
    @emoji_poll.subcommand(
        sub_cmd_name="remove-emoji",
        sub_cmd_description="Make a poll to remove an emoji"
    )
    @slash_option(
        name="emoji",
        description="The emoji you are suggesting to remove",
        opt_type=OptionType.STRING,
        required=True
    )
    async def emoji_poll_remove(self, ctx: SlashContext, emoji: str):
        await ctx.defer(ephemeral=True)

        # Handle polln't
        if self.check_pollnt(ctx.member):
            await ctx.send(embeds=Embed(description=f"You aren't allowed to make polls because you have the polln't role.", color=Color.RED))
            return

        input_emoji_list = [input_emoji['emoji'] for input_emoji in self.custom_emoji_list(emoji)]
        accessible_emojis, inaccessible_emojis = await self.check_accessible_emojis(ctx.guild, input_emoji_list)

        # Check if no custom emoji input
        if len(input_emoji_list) == 0:
            await ctx.send(embed=Embed(title="No Custom Emoji Input", description="You didn't enter a custom emoji! You need to enter one of the servers emojis.", color=Color.RED), ephemeral=True)
            return

        # Check if more than one emoji input
        if len(input_emoji_list) > 1:
            await ctx.send(embed=Embed(title="Multiple Emojis Input", description="You entered multiple emojis! You can only enter one emoji.", color=Color.RED), ephemeral=True)
            return

        # Check if input emoji is inaccessible
        if not accessible_emojis and inaccessible_emojis:
            await ctx.send(embed=Embed(title="External Emoji Entered", description="You entered an emoji from another server! You can only enter emojis from this server.", color=Color.RED), ephemeral=True)
            return

        emoji = accessible_emojis[0]
        emoji_name = emoji.split(":")[1]

        # Make poll to remove it
        # Get the poll channel
        polls_channel_id = Config.get_config_parameter("poll_channel_id")
        if not polls_channel_id:
            await ctx.send(embeds=Embed(description="The poll channel could not be found :sob:. Please notify a staff member", color=Color.RED))
            return

        # Get emoji poll number
        try:
            poll_number = Data.get_data_item("emoji_poll_number")
        except:
            poll_number = 1

        # Send the poll
        embed = Embed(
            title=f"Emoji Poll #{poll_number}",
            description=f"{ctx.author.mention} is suggesting removing the emoji `:{emoji_name}:` {emoji}",
            color=Color.YORANGE,
            author=EmbedAuthor(name=f"{ctx.member.user.username}", icon_url=ctx.member.user.avatar.url),
            footer="The outcome will be decided in 24 Hours!"
        )

        polls_channel = await ctx.guild.fetch_channel(polls_channel_id)
        poll = await polls_channel.send(embed = embed)

        # Increment poll number
        poll_number += 1
        Data.set_data_item("emoji_poll_number", poll_number)

        # Add poll reactions
        for reaction_emoji in ("✅", "❌"):
            await poll.add_reaction(reaction_emoji)

        # Respond to the user
        await ctx.send(embeds=Embed(description="Successfully sent your emoji poll!", color=Color.GREEN), ephemeral=True)

        # Save poll and emoji info to data, as well as end time
        time = datetime.utcnow() + timedelta(days=1)
        Data.set_data_item(key=str(poll.id), value={"channel_id": str(poll.channel.id), "end_time": time.strftime("%d/%m/%Y, %H:%M"), "emoji": emoji}, table="emoji_polls")

        # Log poll
        await logs.DiscordLogger.log_raw(self.bot,f"{ctx.author.mention} {ctx.author.username} created an emoji poll to remove {emoji}")

        self.logger.info(f"{ctx.author.user.username}#{ctx.author.user.discriminator} created an emoji poll to remove {emoji}")

    ### /EMOJI-POLL ADD-EMOJI ###
    @emoji_poll.subcommand(
        sub_cmd_name="add-emoji",
        sub_cmd_description="Make a poll to add an emoji"
    )
    @slash_option(
        name="name",
        description="The name of the emoji you are suggesting",
        opt_type=OptionType.STRING,
        required=True
    )
    @slash_option(
        name="image",
        description="The image of the emoji you suggest adding",
        opt_type=OptionType.ATTACHMENT,
        required=True
    )
    async def emoji_poll_add(self, ctx: SlashContext, name: str, image: Attachment):
        await ctx.defer(ephemeral=True)

        # Handle polln't
        if self.check_pollnt(ctx.member):
            await ctx.send(embeds=Embed(description=f"You aren't allowed to make polls because you have the polln't role.", color=Color.RED))
            return

        # Get emoji numbers so it can be checked if limit is reached
        num_allowed_emojis = ctx.guild.emoji_limit
        all_custom_emojis = await ctx.guild.fetch_all_custom_emojis()
        num_animated_emojis = 0
        
        for emoji in all_custom_emojis:
            if emoji.animated:
                num_animated_emojis += 1

        num_custom_emojis = len(all_custom_emojis) - num_animated_emojis

        # Check that emoji name fits discord requirements
        name = name.strip(":")
        if not self.check_emoji_name(name):
            await ctx.send(embed=Embed(title="Bad emoji name", description=f"The emoji name you entered (`{name}`) does not meet discord's requirements. Emoji names must be longer than 2 characters and contain only alphanumeric characters and underscores.", color=Color.RED), ephemeral=True)
            return
        
        # Check if emoji name already taken
        for emoji in all_custom_emojis:
            if emoji.name.lower() == name.lower():
                await ctx.send(embed=Embed(title="Emoji Name Taken", description=f"An emoji with the name `:{emoji.name}:` already exists. Please choose another name and try again.", color=Color.RED), ephemeral=True)
                return

        # Check that attachment is an image
        if not image.filename.lower().endswith((".png", ".jpeg", ".gif")):
            await ctx.send(embed=Embed(title="Bad emoji file format", description=f"The `.{image.filename.split('.')[-1]}` file format cannot be used. Emoji images must be JPEG, PNG or GIF.", color=Color.RED), ephemeral=True)
            return

        # Check if animated emoji limit reached
        if image.filename.lower().endswith(".gif") and num_animated_emojis >= num_allowed_emojis:
            await ctx.send(embed=Embed(title="Animated emoji limit reached", description=f"The server has already hit the animated emoji limit! To make room for a new animated emoji you could make an emoji poll to remove an existing animated emoji.", color=Color.RED), ephemeral=True)
            return

        # Check if custom emoji limit reached
        if image.filename.lower().endswith((".png", ".jpeg")) and num_custom_emojis >= num_allowed_emojis:
            await ctx.send(embed=Embed(title="Custom emoji limit reached", description=f"The server has already hit the custom emoji limit! To make room for a new custom emoji you could make an emoji poll to remove an existing custom emoji.", color=Color.RED), ephemeral=True)
            return
        
        # Download image
        image_name = name
        image_extension = image.filename.split(".")[-1]
        image_filename = f"emojipoll_{image_name}_{self.next_image_index('emojipoll')}.{image_extension}"
        image_filepath = f"./images/{image_filename}"
        
        response = requests.get(image.url, stream=True)
        
        with open(image_filepath, 'wb') as f:
            f.write(response.content)

        size = os.path.getsize(image_filepath)

        # Check that image is within size limit
        if size > 256000:
            await ctx.send(embed=Embed(title="Image too large", description=f"Discord allows emojis to have a max file size of 256KB! The image you uploaded is `{round(size/1000, 2)}KB`.", color=Color.RED), ephemeral=True)
            return

        # Get the poll channel
        polls_channel_id = Config.get_config_parameter("poll_channel_id")
        if not polls_channel_id:
            await ctx.send(embeds=Embed(description="The poll channel could not be found :sob:. Please notify a staff member", color=Color.RED))
            return

        # Get emoji poll number
        try:
            poll_number = Data.get_data_item("emoji_poll_number")
        except:
            poll_number = 1

        # Send the poll
        embed = Embed(
            title=f"Emoji Poll #{poll_number}",
            description=f"{ctx.author.mention} is suggesting adding the emoji below as `:{name}:`",
            color=Color.YORANGE,
            author=EmbedAuthor(name=f"{ctx.member.user.username}", icon_url=ctx.member.user.avatar.url),
            images=EmbedAttachment(url=f"attachment://{image_filename}"),
            footer="The outcome will be decided in 24 Hours!"
        )

        polls_channel = await ctx.guild.fetch_channel(polls_channel_id)
        poll = await polls_channel.send(embed = embed, file=File(image_filepath))

        # Increment poll number
        poll_number += 1
        Data.set_data_item("emoji_poll_number", poll_number)

        # Add poll reactions
        for emoji in ("✅", "❌"):
            await poll.add_reaction(emoji)

        # Respond to the user
        await ctx.send(embeds=Embed(description="Successfully sent your emoji poll!", color=Color.GREEN), ephemeral=True)

        # Save poll and emoji info to data, as well as end time
        time = datetime.utcnow() + timedelta(days=1)
        Data.set_data_item(key=str(poll.id), value={"channel_id": str(poll.channel.id), "end_time": time.strftime("%d/%m/%Y, %H:%M"), "emoji_image_path": image_filepath, "emoji_name": name}, table="emoji_polls")

        # Log poll
        await logs.DiscordLogger.log_raw(self.bot,f"{ctx.author.mention} {ctx.author.username} created an emoji poll\nName: `{name}`\nimage: `{image.url}`")

        self.logger.info(f"{ctx.author.user.username}#{ctx.author.user.discriminator} created an emoji poll. Name: '{name}', image: '{image.url}'")

    @Task.create(IntervalTrigger(minutes=1))
    async def emoji_remove_poll_finish(self):
        time = datetime.utcnow().replace(second=0, microsecond=0)

        for poll in Data.get_all_items(table="emoji_polls"):
            # Ignore if poll doesn't end now
            if time != datetime.strptime(poll['value']['end_time'], "%d/%m/%Y, %H:%M"):
                return
            
            # Ignore add emoji polls
            if "emoji" not in poll['value']:
                return
            
            # Determine the result of the poll

            # Get poll message
            poll_channel = await self.bot.fetch_channel(poll['value']['channel_id'])
            poll_message = await poll_channel.fetch_message(poll['key'])
            poll_embed = poll_message.embeds[0]

            # Check reactions
            yes_reactions = len(await poll_message.fetch_reaction("✅")) - 1
            no_reactions = len(await poll_message.fetch_reaction("❌")) - 1

            # Edit embed with results and send update message

            # Equal votes
            if no_reactions == yes_reactions:
                poll_embed.color = Color.YORANGE
                poll_embed.description = poll_embed.description + f"\n```Results: Yes ({yes_reactions}), No ({no_reactions})```"
                poll_embed.footer = "This poll has ended. The results were too close to call, so the emoji hasn't been removed."
                await poll_message.edit(embed=poll_embed)
                await poll_channel.send(embed=Embed(description=f"Voting to remove the emoji ({poll['value']['emoji']}) suggested in [{poll_embed.title}]({poll_message.jump_url}) was equal! The results were `Yes ({yes_reactions}), No ({no_reactions})`. Because of this, it will not be removed.", color=Color.YORANGE))    
            
            # Emoji rejected
            if no_reactions > yes_reactions:
                poll_embed.color = Color.RED
                poll_embed.description = poll_embed.description + f"\n```Results: No ({no_reactions}), Yes ({yes_reactions})```"
                poll_embed.footer = "This poll has ended. The suggested emoji was not removed."
                await poll_message.edit(embed=poll_embed)
                await poll_channel.send(embed=Embed(description=f"The emoji suggested for removal ({poll['value']['emoji']}) in [{poll_embed.title}]({poll_message.jump_url}) was not removed! The results were `Yes ({yes_reactions}), No ({no_reactions})`.", color=Color.RED))

            # Emoji accepted
            if yes_reactions > no_reactions:
                # Update embed and send update message
                poll_embed.color = Color.GREEN
                poll_embed.description = poll_embed.description + f"\n```Results: Yes ({yes_reactions}), No ({no_reactions})```"
                poll_embed.footer = "This poll has ended. The suggested emoji was removed."
                await poll_message.edit(embed=poll_embed)
                await poll_channel.send(embed=Embed(description=f"The emoji suggested for removal ({poll['value']['emoji']}) in [{poll_embed.title}]({poll_message.jump_url}) was removed! The results were `Yes ({yes_reactions}), No ({no_reactions})`.", color=Color.GREEN))

                # Remove the emoji
                guild = poll_channel.guild
                the_emoji = await guild.fetch_custom_emoji(int((poll['value']['emoji']).split(":")[-1][:-1]))
                await the_emoji.delete(reason="Emoji Poll")

            # Delete poll data
            Data.delete_item(poll, table="emoji_polls")

    # Removes emoji poll data if the emoji poll is deleted
    @listen("on_message_delete")
    async def on_poll_delete(self, event: MessageDelete):
        # Check if the deleted message is a poll
        poll_channel_id = Config.get_config_parameter("poll_channel_id")
        if str(event.message.channel.id) == poll_channel_id:
            # It was a poll!
            emoji_polls = Data.get_all_items(table="emoji_polls")

            for poll in emoji_polls:
                if str(event.message.id) == poll['key']:
                    Data.delete_item(poll, table="emoji_polls")

    # Task that finished emoji polls
    @Task.create(IntervalTrigger(minutes=1))
    async def emoji_add_poll_finish(self):
        time = datetime.utcnow().replace(second=0, microsecond=0)

        for poll in Data.get_all_items(table="emoji_polls"):
            # Ignore if poll doesn't end now
            if time != datetime.strptime(poll['value']['end_time'], "%d/%m/%Y, %H:%M"):
                return
            
            # Ignore remove emoji polls
            if 'emoji' in poll['value']:
                continue

            # Determine the result of the poll

            # Get poll message
            poll_channel = await self.bot.fetch_channel(poll['value']['channel_id'])
            poll_message = await poll_channel.fetch_message(poll['key'])
            poll_embed = poll_message.embeds[0]

            # Check reactions
            yes_reactions = len(await poll_message.fetch_reaction("✅")) - 1
            no_reactions = len(await poll_message.fetch_reaction("❌")) - 1

            # Edit embed with results and send update message

            emoji_image_file = File(poll['value']['emoji_image_path'])

            # Equal votes
            if no_reactions == yes_reactions:
                poll_embed.color = Color.YORANGE
                poll_embed.description = poll_embed.description + f"\n```Results: Yes ({yes_reactions}), No ({no_reactions})```"
                poll_embed.footer = "This poll has ended. The results were too close to call, so the emoji hasn't been added."
                poll_embed.image = EmbedAttachment(url=f"attachment://{emoji_image_file.file_name}")
                await poll_message.edit(embed=poll_embed, file=emoji_image_file)
                await poll_channel.send(embed=Embed(description=f"Voting for the emoji suggested in [{poll_embed.title}]({poll_message.jump_url}) was equal! The results were `Yes ({yes_reactions}), No ({no_reactions})`. Because of this, it will not be added.", color=Color.YORANGE))    
            
            # Emoji rejected
            if no_reactions > yes_reactions:
                poll_embed.color = Color.RED
                poll_embed.description = poll_embed.description + f"\n```Results: No ({no_reactions}), Yes ({yes_reactions})```"
                poll_embed.footer = "This poll has ended. The suggested emoji was rejected."
                poll_embed.image = EmbedAttachment(url=f"attachment://{emoji_image_file.file_name}")
                await poll_message.edit(embed=poll_embed, file=emoji_image_file)
                await poll_channel.send(embed=Embed(description=f"The emoji suggested in [{poll_embed.title}]({poll_message.jump_url}) was rejected! The results were `Yes ({yes_reactions}), No ({no_reactions})`. It will not be added.", color=Color.RED))

            # Emoji accepted
            if yes_reactions > no_reactions:
                # Add the emoji
                guild = poll_channel.guild
                new_emoji = await guild.create_custom_emoji(name = poll['value']['emoji_name'], imagefile=File(poll['value']['emoji_image_path']), reason="Emoji Poll Accepted")

                # Update embed and send update message
                poll_embed.color = Color.GREEN
                poll_embed.description = poll_embed.description + f"\n```Results: Yes ({yes_reactions}), No ({no_reactions})```"
                poll_embed.footer = "This poll has ended. The suggested emoji was accepted."
                poll_embed.image = EmbedAttachment(url=f"attachment://{emoji_image_file.file_name}")
                await poll_message.edit(embed=poll_embed, file=emoji_image_file)
                await poll_channel.send(embed=Embed(description=f"The emoji suggested in [{poll_embed.title}]({poll_message.jump_url}) was accepted! The results were `Yes ({yes_reactions}), No ({no_reactions})`. It has now been added for everyone to use! `:{new_emoji.name}:`: {new_emoji}{new_emoji}{new_emoji}{new_emoji}{new_emoji}", color=Color.GREEN))

            # Delete poll data and image file
            Data.delete_item(poll, table="emoji_polls")

    # Checks if emoji name meets discord requirements
    def check_emoji_name(self, name):
        return len(name) > 2 and re.match("^[a-zA-Z0-9_]+$", name)
    
    # Gets the next index for an image with the given start string
    def next_image_index(self, start: str):
        directory = './images/'
        files = [f.split(".")[0] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        matching_files = [f for f in files if f.startswith(start)]
        numbers = [int(re.findall(r'^\D*(\d*)$', f)[0]) for f in matching_files if re.findall(r'^\D*(\d*)$', f)]
        
        if numbers:
            return max(numbers) + 1
        
        return 0

    ### /POLL ###
    @slash_command(
        name="poll",
        description="Just a template command",
    )
    @slash_option(
        name="question",
        description="Enter your poll question here",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="emojis",
        description="Enter your poll emojis here",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="image",
        description="Upload an image for your poll",
        required=False,
        opt_type=OptionType.ATTACHMENT
    )
    @slash_option(
        name="anonymous",
        description="Do you want your poll to be anonymous?",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Yes", value="Yes"),
            SlashCommandChoice(name="No", value="")
        ]
    )
    @slash_option(
        name="thread",
        description="Do you want your poll to have an attached thread?",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Yes", value="Yes"),
            SlashCommandChoice(name="No", value="")
        ]
    )
    async def poll_command(self, ctx: SlashContext, question: str, emojis: str = None, image: Attachment = None, anonymous: bool = False, thread: bool = False):
        await ctx.defer(ephemeral=True)

        # Handle polln't
        if self.check_pollnt(ctx.member):
            await ctx.send(embeds=Embed(description=f"You aren't allowed to make polls because you have the polln't role.", color=Color.RED))
            return
        
        # Set default emojis if custom emojis werent specified
        if not emojis:
            emojis = "⬆️ ⬇️ ↕️"

        # Make sure question isn't empty / has words
        if not self.check_valid_question(question):
            await ctx.send(embeds=Embed(description=f"Invalid question: `{question}`.", color=Color.RED))
            return
        
        # Check if inaccessible or duplicate emojis were entered
        emoji_list = self.get_emojis(emojis)
        emoji_list, duplicates = self.check_duplicate_emojis(emoji_list)
        emoji_list, inaccessible = await self.check_accessible_emojis(ctx.guild, emoji_list)

        # If too few emojis entered
        if len(emoji_list) <= 1:
            await ctx.send(embeds=Embed(title="Too Few Emojis Entered", description=f"You entered `{len(emoji_list)}` unique emojis: `{', '.join(emoji_list)}`. To use custom emojis, you need to specify at least two unique emojis.", color=Color.RED))
            return

        # If an inaccessible emoji was entered
        if inaccessible:
            valid_emojis = "- " + "\n- ".join(emoji_list)

            await ctx.send(embeds=Embed(title="Inaccessible Emojis Entered", description=f"Unable to access the following emojis: '{' '.join(inaccessible)}'.", color=Color.RED))
            return

        # If duplicate emojis were entered
        if duplicates:
            valid_emojis = "- " + "\n- ".join(emoji_list)

            embed = Embed(title="Duplicate Emojis Entered",
                description=f"You entered '{' '.join(duplicates)}' multiple times! Would you like to send the poll anyway with the following emojis?\n{valid_emojis}", color=Color.YORANGE)
            
            buttons = [
                Button(style=ButtonStyle.SUCCESS, label="Send Anyway", custom_id=f"send_poll_anyway"),
                Button(style=ButtonStyle.DANGER, label="Don't Send", custom_id=f"dont_send_poll")
            ]

            duplicate_send_anyway_message = await ctx.send(embed = embed, components=buttons, ephemeral=True)

            response = await self.bot.wait_for_component(
                messages=duplicate_send_anyway_message,
                components=buttons
            )

            # Don't send the poll
            if response.ctx.custom_id == "dont_send_poll":
                buttons[0].disabled = True
                buttons[1].disabled = True
                await response.ctx.edit_origin(embeds=Embed(description="Your poll has been cancelled", color=Color.GREEN), components=buttons)
                return
            
            # Send the poll
            buttons[0].disabled = True
            buttons[1].disabled = True
            await response.ctx.edit_origin(embeds=Embed(description="OK! sending your poll...", color=Color.GREEN), components=buttons)

        # Get the poll number
        try:
            poll_number = Data.get_data_item("poll_number")
        except:
            poll_number = 1

        # Create the poll embed
        embed = Embed(title = f"Poll #{poll_number}", description = question, color = Color.GREEN)

        # Set poll author
        if anonymous:
            embed.set_author(
                name=f"Anonymous User", icon_url="https://cdn.discordapp.com/attachments/972473507223056384/986914030130188308/2123041_copy.png")
        else:
            embed.set_author(
                name=f"{ctx.member.user.username}", icon_url=ctx.member.user.avatar.url)

        # Set image if needed
        file = None
        if image:
            response = requests.get(image.url, stream=True)
            with open(f"./images/poll_{image.filename}", 'wb') as f:
                f.write(response.content)

            file = File(f"./images/poll_{image.filename}")
            embed.image = EmbedAttachment(url=f"attachment://poll_{image.filename}")

        # Get the poll channel
        polls_channel_id = Config.get_config_parameter("poll_channel_id")
        if not polls_channel_id:
            await ctx.send(embeds=Embed(description="The poll channel could not be found :sob:. Please notify a staff member", color=Color.RED))
            return

        # Send the poll
        polls_channel = await ctx.guild.fetch_channel(polls_channel_id)
        poll = await polls_channel.send(embed = embed, file=file)

        # Increment poll number
        poll_number += 1
        Data.set_data_item("poll_number", poll_number)

        # Add poll reactions
        for emoji in emoji_list:

            # If custom emoji, remove the '<>' so it can be used
            if emoji.startswith("<"):
                emoji = emoji[1:len(emoji)-1]

            await poll.add_reaction(emoji)

        # Create poll thread if specified
        if thread:
            thread_title = f"Poll Discussion - {question}"
            if len(thread_title) > 100:
                thread_title = thread_title[:97] + "..."

            await polls_channel.create_thread(name=thread_title, auto_archive_duration=1440, message=poll, reason="Poll thread")

        # Respond to the user
        await ctx.send(embeds=Embed(description="Successfully sent your poll!", color=Color.GREEN), ephemeral=True)

        # Delete image if it exists
        if image:
            BotFile(f"./images/poll_{image.filename}").delete()

        if_image = "" if not image else f"image: `{image.url}`"

        # Log anonymous polls
        if anonymous:
            await logs.DiscordLogger.log_raw(self.bot, f"{ctx.author.mention} {ctx.author.username} created an anonymous poll\nQuestion: `{question}`\nEmojis: {', '.join(emoji_list)}\nThread: {thread}\n{if_image}")
        else:
            await logs.DiscordLogger.log_raw(self.bot,f"{ctx.author.mention} {ctx.author.username} created a poll\nQuestion: `{question}`\nEmojis: {', '.join(emoji_list)}\nThread: {thread}\n{if_image}")

        self.logger.info(f"{ctx.author.user.username}#{ctx.author.user.discriminator} created a poll. Question: '{question}', Emojis: {', '.join(emoji_list)}, Thread: {thread}, {if_image}'")

    # Checks if the input emojis are accessible by the bot
    async def check_accessible_emojis(self, guild: Guild, emoji_list):
        guild_emojis = await guild.fetch_all_custom_emojis()

        str_guild_emojis = [str(emoji) for emoji in guild_emojis]
        accessible_emoji_list = []
        inaccessible_emoji_list = []

        for emoji in emoji_list:
            if not emoji.startswith("<") or emoji in str_guild_emojis:
                accessible_emoji_list.append(emoji)
                continue

            inaccessible_emoji_list.append(emoji)             

        return accessible_emoji_list, inaccessible_emoji_list

    # Checks if the input emojis contain any duplicates
    def check_duplicate_emojis(self, emoji_list):
        refined_emoji_list = list(OrderedDict.fromkeys(emoji_list))
        duplicate_emojis = [emoji for emoji in emoji_list if emoji_list.count(emoji) > 1]
        
        return refined_emoji_list, duplicate_emojis

    # Gets a list of emojis from a string
    def get_emojis(self, emoji_string):
        # Extract unicode and custom emojis from the string
        emoji_list = emoji.emoji_list(emoji_string)
        emoji_list += self.custom_emoji_list(emoji_string)

        # Reconstruct emoji order to match the original string
        emoji_list = sorted(emoji_list, key=lambda x: x['match_start'])

        return [emoji['emoji'] for emoji in emoji_list]

    # Gets a list of custom emojis from a string
    def custom_emoji_list(self, emoji_string):
        emoji_list = []
        emoji_start = None
        
        for idx, char in enumerate(emoji_string):
            if char == "<":
                emoji_start = idx
            elif char == ">" and emoji_start is not None:
                emoji_list.append({"match_start": emoji_start, "emoji": emoji_string[emoji_start:idx + 1]})
                emoji_start = None
        
        return emoji_list

    # Checks if a question string contains any text
    def check_valid_question(self, question):
        return not re.match(r'^[_\W]+$', question)

    # Handles responding to a user with the polln't role
    def check_pollnt(self, member: Member):
        pollnt_role_id = Config.get_config_parameter("pollnt_role_id")
        member_role_ids = [str(role.id) for role in member.roles]

        if pollnt_role_id in member_role_ids:
            return True
        
        return False

    ### /CONFIG POLLS SET-CHANNEL ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="polls",
        group_description="polls group command",
        sub_cmd_name="set-channel",
        sub_cmd_description="Set the channel that polls should be sent to"
    )
    @slash_option(
        name="channel",
        description="The channel polls will be sent to",
        opt_type=OptionType.CHANNEL,
        required=True
    )
    async def config_polls_set_channel(self, ctx: SlashContext, channel: GuildChannel):
        Config.set_config_parameter("poll_channel_id", str(channel.id))
        await ctx.send(embed=Embed(description=f"Successfully set the poll channel to {channel.mention}", color=Color.GREEN), ephemeral=True)

    ### /CONFIG POLLS SET-POLLNT ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="polls",
        group_description="polls group command",
        sub_cmd_name="set-pollnt",
        sub_cmd_description="Set the role that makes users unable to make polls"
    )
    @slash_option(
        name="role",
        description="The role that makes users unable to make polls",
        opt_type=OptionType.ROLE,
        required=True
    )
    async def config_polls_set_pollnt(self, ctx: SlashContext, role: Role):
        Config.set_config_parameter("pollnt_role_id", str(role.id))
        await ctx.send(embed=Embed(description=f"Successfully set the polln't role to {role.mention}", color=Color.GREEN), ephemeral=True)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Polls(bot)