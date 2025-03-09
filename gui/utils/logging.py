# utils/logger.py
# Description: Utility functions for setting up and managing logging.

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str, log_file: str = DEFAULT_LOG_FILE, level=logging.INFO):
    """
    Set up a logger with file and console output.
    
    Args:
        name (str): Name of the logger instance.
        log_file (str): Path to the log file.
        level (int): Logging level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():  # Prevent duplicate handlers
        logger.setLevel(level)

        # Log format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

        # File handler (with rotation)
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)  # 5MB max size
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Example Usage:
if __name__ == "__main__":
    logger = setup_logger("app_logger")
    logger.info("✅ Application started")
    logger.warning("⚠️ This is a warning")
    logger.error("❌ An error occurred")
    logger.debug("🔍 Debugging info")
    logger.critical("🔥 Critical error!")
