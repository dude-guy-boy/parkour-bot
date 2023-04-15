# bot.py

import os, asyncio, src.logs as logs, multiprocessing, src.mockserver as mockserver
from dotenv import load_dotenv
from src.files import Directory
from interactions import Client, Intents

# TODO: in-discord logging, universal interaction logging, Backups, Bot restart / reload

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

    # Create base folders
    Directory("./data/").create()
    Directory("./config/").create()
    Directory("./logs/").create()

    logger.info("Starting bot...")

    # Get a list of all extensions
    extensions = [
        module[:-3]
        for module in os.listdir(f"{os.path.dirname(__file__)}/extensions")
        if module not in ("__init__.py", "template.py") and module[-3:] == ".py"
    ]

    # Load all extensions in list
    if extensions != []:
        logger.info(f"Importing {len(extensions)} extension(s): {', '.join(extensions)}")
    else:
        logger.warning("Could not import any extensions!")

    for ext in extensions:
        try:
            bot.load_extension(f"extensions.{ext}")
            logger.info(f"Loaded extension: {ext}")
        except Exception as err:
            logger.error(f"Could not load extension: {ext}")
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