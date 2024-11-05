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
group_id = os.getenv("GROUP_ID")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 2080)
)


async def fetch_group_history():
    logger.info("Started fetching group history")

    dialogs = await client.get_dialogs()

    topic_result = await client(
        functions.channels.GetForumTopicsRequest(
            channel=dialogs[0].entity.id,
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=100,
            # q='some string here'
        )
    )

    topics = {
        topic.id: {"title": topic.title, "top_msg_id": topic.top_message, "msgs": []}
        for topic in topic_result.topics
    }

    users = []
    async for user in client.iter_participants(entity=dialogs[0].entity):
        users.append(user)
        full = await client(GetFullUserRequest(user))
        bio = full.full_user.about
        bday = (
            f"{full.full_user.birthday.year}-{full.full_user.birthday.month}-{full.full_user.birthday.day}"
            if full.full_user.birthday is not None
            else None
        )
        user_id = user.id

        # save user
        cursor.execute(
            """
                INSERT INTO users (id, first_name, last_name, username, phone, bday, bio, is_verified, is_bot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                user.first_name,
                user.last_name,
                user.username,
                user.phone,
                bday,
                bio,
                user.verified,
                user.bot,
            ),
        )
        # Commit the transaction to save changes
        conn.commit()
        print(f"{user.username}:{user_id} - Saved")

        photos = await client.get_profile_photos(user)

        # Download each profile photo
        for i, photo in enumerate(photos):
            # Generate a filename for each photo
            file_path = f"profile_pics/{user.id}_{i}.jpg"

            # Download the photo
            await client.download_media(photo, file_path)

            # save in db
            cursor.execute(
                """
                INSERT INTO avatars (id, user_id, path)
                VALUES (?, ?, ?)
            """,
                (photo.id, user_id, file_path),
            )
            # Commit the transaction to save changes
            conn.commit()
            print(f"Downloaded {file_path}")

    print(len(users))

    """
        bot bool
        first_name str
        id int
        last_name str
        username str
        phone str
        verified bool
    """


# Start the Telegram client


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
