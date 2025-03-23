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
conn.set_trace_callback(print)

cursor = conn.cursor()

# Use your own values from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
dialog_title = os.getenv("GROUP_TITLE")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 2080)
)

old_data_dir = "users_feb.csv"
old_data = pd.read_csv(old_data_dir)


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
            users.append(user.id)

        # df = pd.DataFrame(users)
        # df.to_csv("users.csv")
        print(len(users))

        users_df = pd.DataFrame(columns=["user_id"])
        users_df["user_id"] = users
        users_df.to_csv("users_mar.csv", index=False)

    gone_users = []
    for idx, row in old_data.iterrows():
        if row["user_id"] not in users:
            cursor.execute("SELECT * FROM users WHERE id = ?",
                           (str(row["user_id"]),))
            user = cursor.fetchone()
            if user is not None:
                this_dict = {
                    "user_id": row["user_id"],
                    "username": user[3],
                    "name": f"{user[1]} {user[2]}",
                }

                gone_users.append(this_dict)

    gone_df = pd.DataFrame(gone_users)

    gone_df.to_csv("gone_feb.csv", index=False)

    logger.info("Finished fetching group history")


# Start the Telegram client


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
