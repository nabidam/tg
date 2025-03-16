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
from utils import save_user
import pandas as pd

load_dotenv()

os.makedirs("avatars", exist_ok=True)

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


# conn = sqlite3.connect("db.db")
# conn.set_trace_callback(print)

# cursor = conn.cursor()

# Use your own values from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
dialog_title = os.getenv("GROUP_TITLE")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 8080)
)


# users_df = pd.DataFrame(
#     columns=["id", "tg_id", "username", "first_name", "last_name", "avatar"])


async def fetch_group_history():
    logger.info("Started fetching group history")

    dialogs = await client.get_dialogs()

    cc = None
    for d in dialogs:
        if d.title == dialog_title:
            cc = d
            break

    if cc:
        users = []
        async for user in client.iter_participants(entity=cc.entity):
            print(
                f"[INFO] processing user {user.id}, with username {user.username}")
            photos = await client.get_profile_photos(user)

            # Download each profile photo
            file_path = None
            if len(photos):
                photo = photos[0]

                file_path = f"avatars/{user.id}.jpg"

                # if not os.path.exists(file_path):
                # Download the photo
                await client.download_media(photo, file_path)

                print(f"Downloaded {file_path}")

            this_user = {
                "tg_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": None if not file_path else "static/" + file_path
            }
            users.append(this_user)

        # df = pd.DataFrame(users)
        # df.to_csv("users.csv")
        print(len(users))

        users_df = pd.DataFrame(users)
        users_df.to_csv("users_for_par3.csv", index=False)

    logger.info("Finished fetching group history")


# Start the Telegram client


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
