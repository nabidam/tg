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

df = pd.read_csv("vashers.csv")

result = df.groupby("username").size().reset_index(name="count")
result = result.sort_values(by="count", ascending=True)
result = result[["username", "count"]]

result.to_csv("stats_vasher.csv", index=False)
