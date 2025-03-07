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
from utils import save_msg_file
from time import sleep
import shutil

load_dotenv()

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

# Use your own values from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
group_title = os.getenv("DL_GP_TITLE")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 2080)
)

# TODO: limit large files


async def fetch_group_history():
    logger.info("Started fetching group history")

    dialogs = await client.get_dialogs()

    cc = None
    for d in dialogs:
        if d.title == group_title:
            cc = d
            break

    if cc:
        last_msg_id = None
        # current_msg_id = latest_msg[0]
        current_msg_id = 0
        messages = []
        while current_msg_id != last_msg_id:
            async for message in client.iter_messages(
                cc.entity.id, limit=1000, offset_id=current_msg_id
            ):
                print(f"[INFO] Processing msg_id: {message.id}")
                # check for disk
                total, used, free = shutil.disk_usage("/home/navid")
                if free < 1024 * 1024 * 100:
                    raise RuntimeError(
                        "Disk space is below 100 MB! Exiting application."
                    )
                # print(message)
                await save_msg_file(message, client, "farayande")
                # Log message details
                logger.info(
                    f"Message from user {message.sender_id} at {message.date}: {message.text}"
                )

                # if message.document or message.file or message.forward:
                #     print("got")

                # if message.reply_to is None:
                #     print(f"Message: {message.message}")
                #     print(f"is in GENERAL")
                #     continue
                last_msg_id = current_msg_id
                current_msg_id = message.id

                # msg = {
                #     "id": message.id,
                #     "message": message.message,
                #     "raw_text": message.raw_text,
                #     "topic_id": (
                #         message.reply_to.reply_to_top_id
                #         if message.reply_to.reply_to_top_id is not None
                #         else message.reply_to_msg_id
                #     ),
                #     "reply_to": message.reply_to_msg_id,
                #     "from_id": message.from_id.user_id,
                #     "date": message.date,
                # }

                # topics[msg["topic_id"]]["msgs"].append(msg)
                # print(f"Message: {message.text}")

            # # Optionally log replies and mentions
            # if message.is_reply:
            #     logger.info(f"Message {message.id} is a reply to message {
            #                 message.reply_to_msg_id}")
            # if message.mentions:
            #     logger.info(f"Message {message.id} contains mentions: {
            #                 message.mentioned_ids}")
        print(f"SLEEPING 3s Zzzzz.")
        sleep(3)

    logger.info("Finished fetching group history")


# Start the Telegram client


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
