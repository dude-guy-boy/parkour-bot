# manager.py

from interactions import (
    Client,
    Extension,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    AutocompleteContext,
    File as InteractionsFile,
    Task,
    TimeTrigger,
    IntervalTrigger,
    SlashCommand,
    SlashCommandChoice
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Data
from src.files import File, Directory
from src.customsend import send, edit
from datetime import datetime
from os import execl, kill
from sys import executable, argv
from signal import SIGKILL
from git import Repo
import shutil
import os
import subprocess

class Manager(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

        # Create the repo object
        self.repo = Repo('.')
        assert not self.repo.bare

        self.hourly_backups.start()
        self.daily_backup_cleanup.start()

    # Base bot command
    bot = SlashCommand(name="bot", description="base bot command")

    ### /BOT BACKUP ###
    @bot.subcommand(
        sub_cmd_name="backup",
        sub_cmd_description="Saves a new backup of the bot"
    )
    async def bot_backup(self, ctx: SlashContext):
        # Do backup
        backup = self.do_backup()

        # Send backup
        await ctx.send(embed=Embed(description="Here's your backup!", color=Color.GREEN), file=InteractionsFile(backup), ephemeral=True)

    ### /BOT RESTART ###
    @bot.subcommand(
        sub_cmd_name="restart",
        sub_cmd_description="Restarts the bot"
    )
    async def bot_restart(self, ctx: SlashContext):
        await self.restart(ctx)

    ### /BOT UPDATE ###
    @bot.subcommand(
        sub_cmd_name="update",
        sub_cmd_description="Updates the bot"
    )
    async def bot_update(self, ctx: SlashContext):
        pulling_msg = await send(ctx, "Pulling repository...", color=Color.YORANGE)

        try:
            # Do the pull
            git = self.repo.git
            pull = git.pull()

            # Format the pull
            split_string = pull.split('\n')
            formatted_string = ''
            for line in split_string:
                line = line.lstrip()
                formatted_string = f"{formatted_string}\n> {line}"

            # Send updates
            await edit(pulling_msg, formatted_string)

            # Log the update
            await logs.DiscordLogger.log_raw(self.bot, description=f"Updated Bot.{formatted_string}")

            reformatted = formatted_string.replace('\n', ':')
            self.logger.info(f"Pulled repository. {reformatted}")

            # Update dependencies
            update_deps = await send(ctx, "Updating dependencies...", color=Color.YORANGE, to_channel=True)
            requirements_str, success = self.install_dependencies_from_requirements()
            await update_deps.edit(embed=Embed(description=requirements_str, color=Color.GREEN if success else Color.RED))

            await self.restart(ctx)
        except:
            await send("Failed to pull updates", color=Color.RED)
            self.logger.warning("Failed to pull repository")
            await logs.DiscordLogger.log(self.bot, ctx, "Failed to pull repository")

    ### /BOT RESTART ###
    async def restart(self, ctx: SlashContext):
        # Set channel where message should be sent on startup
        Data.set_data_item("restart_channel", str(ctx.channel.id))
        await ctx.channel.send(embeds=Embed(description="Restarting...", color=Color.YORANGE))
        self.logger.info("Restarting bot & socket server")

        # Kill server process so it will also be restarted
        server_process_id = Data.get_data_item("server_process_id")
        kill(server_process_id, SIGKILL)

        # Restarts bot
        execl(executable, *([executable]+argv))

    @bot.subcommand(
        sub_cmd_name="get-backup",
        sub_cmd_description="Get an old backup"
    )
    @slash_option(
        name="folder",
        description="The time period the backup you want is from",
        opt_type=OptionType.STRING,
        required=True,
        choices=[
            SlashCommandChoice(name="Today", value="./backups/today"),
            SlashCommandChoice(name="Older", value="./backups/older")
        ]
    )
    @slash_option(
        name="backup",
        description="The backup you want to get",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
    )
    async def bot_get_backup(self, ctx: SlashContext, folder: str, backup: str):
        if not backup:
            await ctx.send(embed=Embed(description="That's not a backup!", color=Color.RED), ephemeral=True)
            return
        
        await ctx.send(file=InteractionsFile(backup), ephemeral=True)

    ### Backup file autocomplete ###
    @bot_get_backup.autocomplete("backup")
    async def backup_files_autocomplete(self, ctx: AutocompleteContext):
        choices = []

        try:
            backup_dir = Directory(ctx.kwargs['folder'])
            contents = backup_dir.contents_long()

            if not contents:
                choices.append({"name": "This folder has no backups.", "value": ""})

            for file in contents:
                choices.append({"name": file.split("/")[-1][:-4], "value": file})
        except:
            choices.append({"name": "Please choose a folder first!", "value": ""})

        filtered_choices = []
        for choice in choices:
            if ctx.input_text.lower() in choice['name'].lower():
                filtered_choices.append(choice)

        await ctx.send(filtered_choices[:25])

    ### /BOT GET-LOGS ###
    @bot.subcommand(
        sub_cmd_name="get-logs",
        sub_cmd_description="Get logs from a specific date"
    )
    @slash_option(
        name="date",
        description="The date you want logs for",
        opt_type=OptionType.STRING,
        autocomplete=True,
        required=True
    )
    async def bot_get_logs(self, ctx: SlashContext, date: str):
        if date == "Latest":
            # Get latest filepath
            path = "./logs"
            files = os.listdir(path)
            paths = [os.path.join(path, basename) for basename in files]
            date = max(paths, key=os.path.getctime)
    
        # Send file if it exists
        log_file = File(date)
        if log_file.exists():
            await ctx.send(file = InteractionsFile(date), ephemeral = True)
            # await self.discord_logger.log_command(ctx, f"Sent log file: {log_file_name}")
            self.logger.info(f"Sent log file: {date}")
            return

        # If filepath invalid
        await ctx.send(
            embeds=Embed
            (
                description="That date is invalid! Please select a date from the provided list in the command", color=Color.RED),
                ephemeral=True
            )                    
        self.logger.info("Invalid Date")

    ### Log files autocomplete ###
    @bot_get_logs.autocomplete("date")
    async def log_files_autocomplete(self, ctx: AutocompleteContext):
        choices = []

        try:
            file_names = os.listdir(
                f"./logs/")
        except:
            file_names = ["No Files Found"]

        for idx, filename in enumerate(file_names):
            file_names[idx] = "./logs/" + filename

        sorted_file_list = sorted(file_names, key=os.path.getctime, reverse=True)

        sorted_file_list.insert(0, "Latest")

        for filename in sorted_file_list:
            choices.append(
                {
                    "name": filename.replace("./logs/", "").replace(".log", ""),
                    "value": filename
                }
            )

        filtered_choices = []
        for choice in choices:
            if ctx.input_text.lower() in choice['name'].lower():
                filtered_choices.append(choice)

        await ctx.send(filtered_choices[:25])

    def do_backup(self):
        time = datetime.utcnow()
        backup_filepath = f'./backups/today/{time.strftime("%d-%m-%Y_%H-%M")}'

        # Create backup directories if they don't exist
        Directory("./backups").create()
        Directory("./backups/today").create()
        Directory("./backups/older").create()

        # Make folder in backups directory for new backup
        temp_dir = Directory(backup_filepath)
        temp_dir.create()

        # Copy config & data folders into it
        shutil.copytree('./data', f"{backup_filepath}/data", ignore=shutil.ignore_patterns('images'))
        shutil.copytree('./config', f"{backup_filepath}/config")

        # Compress it and delete old folder
        shutil.make_archive(backup_filepath, 'zip', backup_filepath)
        temp_dir.delete()

        # Log
        self.logger.info(f"Created a new backup: '{backup_filepath}.zip'")
        
        # Return the backup
        return backup_filepath + ".zip"

    ### Daily Backup Cleanup ###
    @Task.create(
        TimeTrigger(
            hour=0,
            utc=True
        )
    )
    def daily_backup_cleanup(self):
        # Clean up daily backups
        today = Directory("./backups/today")
        today.create()

        files = today.contents_long()
        files = [file for file in files if file.endswith(".zip")]

        latest_backup = max(files, key=os.path.getctime)

        shutil.move(latest_backup, f"./backups/older/{latest_backup.split('/')[-1]}")
        today.delete()

        self.logger.info(f"Day finished, cleaned up daily backups")

    ### Hourly Backups Task ###
    @Task.create(IntervalTrigger(hours=1))
    async def hourly_backups(self):
        self.logger.info("Backing-up...")

        self.do_backup()

        self.logger.info("Backup created")

    def install_dependencies_from_requirements(self):
        try:
            subprocess.check_call(['pip', 'install', '-r', './requirements.txt'])
            return "All dependencies updated successfully.", True
        except subprocess.CalledProcessError as e:
            return f"Failed to install dependencies. Error: {str(e)}", False

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Manager(bot)