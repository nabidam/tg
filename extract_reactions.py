import argparse
import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from time import sleep
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest

load_dotenv()

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
group_title = os.getenv("GROUP_TITLE")

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 2080)
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process user activity with optional topic and date filters."
    )

    # Required argument
    parser.add_argument(
        "--user_id", type=int, required=True, help="User ID (bigint integer, required)"
    )

    # Optional arguments
    parser.add_argument(
        "--topic_id",
        type=int,
        required=False,
        help="Topic ID (bigint integer, optional)",
    )

    parser.add_argument(
        "--date",
        type=str,
        required=False,
        default="1M",
        help="Time period (e.g., '1D' for 1 day, '2M' for 2 months). Default: '1M'",
    )

    return parser.parse_args()


def validate_date_format(date_str):
    """Validate that date string is in format nD or nM where n is a positive integer"""
    if not date_str:
        return False

    if len(date_str) < 2:
        return False

    # Last character should be D or M
    unit = date_str[-1].upper()
    if unit not in ["D", "M"]:
        return False

    # Everything except last character should be digits
    number_part = date_str[:-1]
    if not number_part.isdigit() or int(number_part) <= 0:
        return False

    return True


async def fetch_reactions():
    logger.info("Started fetching reactions...")

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
                messages.append(message)
                last_msg_id = current_msg_id
                current_msg_id = message.id
            print(f"SLEEPING 3s Zzzzz.")
            sleep(3)

    logger.info("Finished fetching reactions.")


async def main():
    args = parse_arguments()

    # Validate date format
    if not validate_date_format(args.date):
        print(
            f"Error: Invalid date format '{args.date}'. Expected format: nD (days) or nM (months), e.g., 1D, 3M"
        )
        sys.exit(1)

    # Extract values
    user_id = args.user_id
    topic_id = args.topic_id
    date_period = args.date

    # Display parsed arguments (for demonstration)
    print(f"User ID: {user_id}")
    print(f"Topic ID: {topic_id if topic_id is not None else 'Not provided'}")
    print(f"Date Period: {date_period}")

    await client.start()
    logger.info("Connected to Telegram API")

    await fetch_group_history()
    logger.info("Group history fetched successfully")


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
