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
from tqdm import tqdm

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

df = pd.read_csv("vashers.csv")

output_file = open("output.jsonl", "r")
faals = [json.loads(jline) for jline in output_file.read().splitlines()]

for idx, row in tqdm(df.iterrows(), total=len(df)):
    for faal_obj in faals:
        if faal_obj["custom_id"] == row["task_id"]:
            df.loc[idx, "faal"] = (
                faal_obj["response"]["body"]["choices"][0]["message"]["content"]
                .replace("\n", " ")
                .replace("\r", " ")
            )

df.to_csv("vashers_with_faal.csv", index=False)
