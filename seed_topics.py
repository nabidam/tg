import logging
from logging.handlers import TimedRotatingFileHandler
from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest
from dotenv import load_dotenv
import datetime
import os
import sqlite3

load_dotenv()

os.makedirs("profile_pics", exist_ok=True)

# Directory to store log files
log_dir = "logs"

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Set up the logger
logger = logging.getLogger("telegram_logger")
logger.setLevel(logging.INFO)

# Create a log handler that rotates daily
log_file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "telegram_logs.log"),
    when="midnight",  # Rotate logs at midnight every day
    interval=1,
    backupCount=7,  # Keep the last 7 log files
    utc=True,  # Use UTC time for logging
)

# Set the log file name format to include the date in the filename
log_file_handler.suffix = "%Y-%m-%d"

# Set the format for log messages
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(log_file_handler)


conn = sqlite3.connect("db.db")

cursor = conn.cursor()

# Use your own values from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
dialog_title = os.getenv("GROUP_TITLE")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 2080)
)


async def fetch_group_history():
    logger.info("Started fetching group history")

    dialogs = await client.get_dialogs()

    cc = None
    for d in dialogs:
        if d.title == dialog_title:
            cc = d
            break

    if cc:
        topic_result = await client(
            functions.channels.GetForumTopicsRequest(
                channel=cc.entity.id,
                offset_date=0,
                offset_id=0,
                offset_topic=0,
                limit=100,
                # q='some string here'
            )
        )

        for topic in topic_result.topics:
            topic_id = topic.id
            cursor.execute("SELECT 1 FROM topics WHERE id = ?", (topic_id,))
            exists = cursor.fetchone() is not None

            if not exists:
                # save topic
                cursor.execute(
                    """
                        INSERT INTO topics (id, title)
                        VALUES (?, ?)
                """,
                    (topic.id, topic.title),
                )
                # Commit the transaction to save changes
                conn.commit()
                print(f"{topic.id}:{topic.title} - Saved")

    logger.info("Finished storing topics")


# Start the Telegram client


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
