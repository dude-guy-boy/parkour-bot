# bot.py

import os, asyncio, src.logs as logs, multiprocessing, src.mockserver as mockserver
import pathlib, os.path
from dotenv import load_dotenv
from src.files import Directory
from src.database import Data
from interactions import Client, Intents
from interactions.ext import prefixed_commands, hybrid_commands

# TODO: universal interaction logging

async def main():
    load_dotenv()

    # Get token from .env
    TOKEN = None
    if not (TOKEN := os.environ.get("TOKEN")):
        TOKEN = None

    # Get debug scope from .env
    DEBUG_SCOPE = None
    if not (DEBUG_SCOPE := os.environ.get("DEBUG_SCOPE")):
        DEBUG_SCOPE = None

    # Init loggers
    logger = logs.init_logger()

    # Create bot instance
    bot = Client(
        token = TOKEN,
        auto_defer = False,
        intents = Intents.DEFAULT | Intents.MESSAGE_CONTENT,
        debug_scope = DEBUG_SCOPE,
        disable_dm_commands = True,
        basic_logging = False,
        # logger = logger
        )
    
    prefixed_commands.setup(bot, default_prefix=['p!', 'P!'])
    hybrid_commands.setup(bot)

    # Create base folders
    Directory("./data/").create()
    Directory("./config/").create()
    Directory("./logs/").create()

    logger.info("Starting bot...")

    # Get a list of all extensions
    extensions = pathlib.Path(f"{os.path.dirname(__file__)}/extensions")
    extensions = [{"name": path.stem, "ext-path": os.path.relpath(path=path, start="./").replace("/", ".")[:-3]} for path in extensions.rglob("*.py") if path.name not in ("__init__.py", "template.py")]

    # Load all extensions in list
    if extensions:
        logger.info(f"Importing {len(extensions)} extension(s): {', '.join([ext['name'] for ext in extensions])}")
    else:
        logger.warning("Could not import any extensions!")

    for ext in extensions:
        try:
            bot.load_extension(ext['ext-path'])
            logger.info(f"Loaded extension: {ext['name']}")
        except Exception as err:
            logger.error(f"Could not load extension: {ext['name']}")
            print(err.with_traceback(None))

    # Start bot
    await bot.astart()

def start():
    '''Creates asyncio loop and starts the bot'''
    asyncio.run(main())

if __name__ == "__main__":
    # Create server and bot processes
    server_process = multiprocessing.Process(name="server", target=mockserver.start)
    bot_process = multiprocessing.Process(name="bot", target=start)
    
    # Start processes
    server_process.start()
    bot_process.start()

    # Set the server process id so that it can be restarted whenever the whole bot is restarted
    Data.set_data_item(key="server_process_id", value=server_process.pid, name="manager")