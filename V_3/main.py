#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import logging
import subprocess
import time
import requests
import os
import signal
import sys

from gui.main_window import DownloaderApp  # Import GUI

# ------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------
LOG_FILE = "app.log"

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# File handler: log everything (DEBUG and above) to app.log
file_handler = logging.FileHandler(LOG_FILE, mode="a")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Stream handler: also output logs to console
stream_handler = logging.StreamHandler(sys.stdout)
stream_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

# ------------------------------------------------------------------------
# run_rust_backend: Start the Rust backend
# ------------------------------------------------------------------------
def run_rust_backend():
    """
    Starts the Rust backend server as a subprocess.
    Checks the /health endpoint to verify the backend is running.
    """
    rust_project_path = "/Users/serageldinattia/Downloads/Advanced-DOW-main/my_project"

    if not os.path.exists(rust_project_path):
        logger.critical(f"❌ Rust project path does not exist: {rust_project_path}")
        messagebox.showerror("Backend Server Error", "Rust project path is incorrect!")
        return None

    try:
        logger.info("Checking if Cargo is installed...")
        cargo_check = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        if cargo_check.returncode != 0:
            raise FileNotFoundError("Cargo (Rust) is not installed or not found in system path.")

        logger.info("Building Rust backend before running it...")
        build_process = subprocess.run(["cargo", "build"], cwd=rust_project_path, capture_output=True, text=True)
        if build_process.returncode != 0:
            logger.critical("Cargo build failed! Check Rust project for errors.")
            messagebox.showerror("Backend Server Error", "Rust project failed to compile. Fix errors and try again.")
            return None

        logger.info("Starting Rust backend server...")
        rust_process = subprocess.Popen(
            ["cargo", "run"],
            cwd=rust_project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Run in a new process group for clean termination
        )

        max_retries = 5
        retry_delay = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get("http://127.0.0.1:8080/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Rust server started successfully on attempt {attempt}.")
                    return rust_process
            except requests.exceptions.RequestException:
                logger.error(f"⚠️ Attempt {attempt}: Rust backend not responding.", exc_info=True)
            time.sleep(retry_delay)

        logger.error("❌ Failed to start Rust backend after 5 attempts.")
        messagebox.showerror("Backend Server Error", "Rust backend failed to start.")
        return None

    except FileNotFoundError as e:
        logger.critical("Cargo is not installed or not in system path.", exc_info=True)
        messagebox.showerror("Backend Server Error", str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error starting Rust backend.", exc_info=True)
        messagebox.showerror("Backend Server Error", str(e))
        return None

# ------------------------------------------------------------------------
# on_close: Cleanly shut down backend and GUI
# ------------------------------------------------------------------------
def on_close(rust_process, root):
    logger.info("🛑 Closing application.")
    if rust_process:
        try:
            logger.info("🔻 Stopping Rust backend...")
            os.killpg(os.getpgid(rust_process.pid), signal.SIGTERM)
            rust_process.wait(timeout=5)
            logger.info("✅ Rust backend process terminated.")
        except ProcessLookupError:
            logger.warning("⚠️ Rust backend process already stopped.")
        except Exception as e:
            logger.error("❌ Failed to terminate Rust process.", exc_info=True)
    root.destroy()

# ------------------------------------------------------------------------
# main: Main entry point for the application
# ------------------------------------------------------------------------
def main():
    try:
        logger.info("Starting Advanced Downloader application.")
        rust_process = run_rust_backend()
        if rust_process is None:
            logger.warning("Continuing without a running Rust backend server.")

        # Create the main application window and GUI
        root = tk.Tk()
        app = DownloaderApp(root)

        # Bind window close event to ensure clean shutdown
        root.protocol("WM_DELETE_WINDOW", lambda: on_close(rust_process, root))

        root.mainloop()
        logger.info("Application closed successfully.")
    except Exception as e:
        logger.error("An unexpected error occurred in the main loop.", exc_info=True)
        messagebox.showerror("Application Error", str(e))

if __name__ == "__main__":
    logger.info("Starting Advanced Downloader...")
    main()
