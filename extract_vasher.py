import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
import datetime
import os
import sqlite3
from utils import save_message
from time import sleep
import shutil
import pandas as pd
import re
import emoji
import json

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


def is_only_emojis(text):
    """
    Check if a string contains only emojis.
    """
    return all(char in emoji.EMOJI_DATA for char in text)


def replace_emojis_with_space(text):
    """
    Replace all emojis in a string with a space.
    """
    return "".join(" " if char in emoji.EMOJI_DATA else char for char in text)


vasher_id = 99268

conn = sqlite3.connect("db.db")
cursor = conn.cursor()

cursor.execute(
    """
SELECT messages.id, messages.raw_text, users.id, users.first_name, users.last_name, users.username 
FROM messages 
JOIN users ON users.id = messages.sender_id 
WHERE 
    (topic_id = ? OR reply_to = ?) AND 
    (has_file = 0 AND is_sticker = 0)
""",
    (vasher_id, vasher_id),
)
vashers = cursor.fetchall()

data = []
batch_tasks = []

system_prompt = """
تو یک مفسر شعر فارسی هستی و بایستی تحلیل و فال مد نظر از روی متن شعر را پاسخ بدهی. مانند فال حافظ عمل کن. تفسیر و مظمون فال را کوتاه و در سه بخش ارائه کن. در جمله اول مثبت و منفی بودن آن را مشخص کن. در جمله دوم پیشگویی در رابطه با مظمون شعر تحلیل کن. در جمله آخر جمع‌بندی انجام بده.
"""

for idx, vasher in enumerate(vashers):
    print(vasher)
    if idx < 16:
        continue

    msg = vasher[1]
    if not msg:
        continue

    # remove @mention
    msg = re.sub(r"@\w+", "", msg).strip()

    msg = replace_emojis_with_space(msg)

    msg = re.sub(r"\s+", " ", msg).strip()

    # check for emoji
    if is_only_emojis(msg) or len(msg) < 20:
        continue

    first_name = vasher[3] if vasher[3] else ""
    last_name = vasher[4] if vasher[4] else ""

    # batch
    task_id = f"faal-{idx}"
    task = {
        "custom_id": task_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            # This is what you would have in your Chat Completions API call
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg},
            ],
        },
    }

    batch_tasks.append(task)

    new_row = {
        "id": vasher[0],
        "user_id": vasher[2],
        "username": vasher[5],
        "message": vasher[1],
        "sender": first_name + " " + last_name,
        "task_id": task_id,
        "faal": "",
    }

    data.append(new_row)

df = pd.DataFrame(data)

df.to_csv("vashers.csv", index=False)

file_name = "batch.jsonl"

with open(file_name, "w", encoding="utf8") as file:
    for obj in batch_tasks:
        file.write(json.dumps(obj, ensure_ascii=False) + "\n")
