import argparse
import sys
import os
import logging
from datetime import datetime, timedelta
import re
from logging.handlers import TimedRotatingFileHandler
from time import sleep
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import (
    CheckChatInviteRequest,
    GetMessageReactionsListRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    PeerChannel,
    PeerChat,
    MessageReactions,
    ReactionEmoji,
    ReactionCustomEmoji,
)

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


def make_naive(dt):
    """Convert timezone-aware datetime to naive by removing tzinfo."""
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def parse_date_spec(date_str):
    """
    Parse date spec like '1D', '2M' into a timedelta or equivalent.
    Returns: (unit, quantity) e.g., ('D', 1), ('M', 3)
    """
    if not date_str:
        return None, None

    match = re.match(r"^(\d+)([DM])$", date_str.upper())
    if not match:
        return None, None

    quantity = int(match.group(1))
    unit = match.group(2)
    return unit, quantity


def get_date_range(date_spec):
    """
    Given a date spec like '1M' or '5D', returns (start_date, end_date)
    where end_date = now, and start_date = now - delta
    """
    unit, quantity = parse_date_spec(date_spec)
    if not unit:
        raise ValueError(f"Invalid date spec: {date_spec}")

    now = datetime.now()
    if unit == "D":
        start_date = now - timedelta(days=quantity)
    elif unit == "M":
        # Approximate: subtract quantity * 30 days (for simplicity)
        # For production, consider using `dateutil.relativedelta`
        start_date = now - timedelta(days=quantity * 30)
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    return start_date, now


def is_date_in_range(date_to_check, date_spec):
    """
    Check if a datetime object falls within the range defined by date_spec.
    Handles both naive and aware datetimes by converting to naive.
    """
    try:
        start_date, end_date = get_date_range(date_spec)

        # Strip timezone info for safe comparison
        date_to_check = make_naive(date_to_check)
        start_date = make_naive(start_date)
        end_date = make_naive(end_date)

        return start_date <= date_to_check <= end_date
    except ValueError:
        return False


def validate_date_format(date_str):
    """Validate that date string is in format nD or nM"""
    unit, quantity = parse_date_spec(date_str)
    return unit is not None


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process user activity with optional topic and date filters."
    )

    # Required argument
    parser.add_argument(
        "--user_id", type=int, required=False, help="User ID (bigint integer, required)"
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


async def fetch_reactions(user_id=575570675, topic_id=None, date_period=None):
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
        reactions = {}
        done = False
        while current_msg_id != last_msg_id and not done:
            async for message in client.iter_messages(
                cc.entity.id, limit=1000, offset_id=current_msg_id
            ):
                print(f"[INFO] Processing msg_id: {message.id}")
                messages.append(message)
                sender = message.sender

                in_range = is_date_in_range(message.date, date_period)

                if not in_range:
                    logger.info("All messages in the date range analized.")
                    done = True
                    break

                if message.reactions:
                    reactions_counts = [ra.count for ra in message.reactions.results]
                    reactions_count = sum(reactions_counts)
                    # print(f"Total reactions: {reactions_count}")
                    for reaction_count in message.reactions.results:
                        emoji = (
                            reaction_count.reaction.emoticon
                            if isinstance(reaction_count.reaction, ReactionEmoji)
                            else "[Custom]"
                        )
                        # print(f"Emoji: {emoji} | Count: {reaction_count.count}")

                    result = await client(
                        GetMessageReactionsListRequest(
                            peer=cc.entity, id=message.id, limit=100
                        )
                    )

                    for ra in result.reactions:
                        if ra.peer_id.user_id == user_id:
                            if sender.id in reactions:
                                reactions[sender.id]["count"] += 1
                            else:
                                reactions[sender.id] = {
                                    "count": 1,
                                    "username": sender.username,
                                    "first_name": sender.first_name,
                                    "last_name": sender.last_name,
                                }
                    # result = await client(GetReactionsRequest(
                    #     peer=chat,
                    #     id=message.id,
                    #     limit=100  # adjust as needed
                    # ))
                    # print(result)
                last_msg_id = current_msg_id
                current_msg_id = message.id

                # sleep(1)
            print(f"SLEEPING 3s Zzzzz.")
            sleep(3)

        print(reactions)
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

    await fetch_reactions(user_id, topic_id, date_period)
    logger.info("Group history fetched successfully")


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
