import logging

def setup_logging():
    """Set up the logging configuration for the application."""
    logging.basicConfig(
        level=logging.INFO,  # Set the default log level to INFO (can also be DEBUG, ERROR, etc.)
        format="%(asctime)s - %(levelname)s - %(message)s",  # Define log message format
        handlers=[
            logging.FileHandler("app.log"),  # Log to a file (app.log)
            logging.StreamHandler()  # Log to console
        ]
    )
