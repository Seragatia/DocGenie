import tkinter as tk
from tkinter import messagebox
import logging
import subprocess
import time
import requests
from gui.main_window import DownloaderApp

# ✅ Improved Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    filename="app.log",
    filemode="a",  # Append to log file
)


def run_rust_backend():
    """Runs the Rust backend server as a subprocess."""
    try:
        logging.info("Starting Rust backend server...")
        rust_process = subprocess.Popen(
            ["cargo", "run", "--bin", "my_project"], 
            cwd="/Users/serageldinattia/Downloads/Advanced-DOW-main/my_project"
        )

        retries = 5
        while retries > 0:
            try:
                response = requests.get("http://127.0.0.1:8080", timeout=5)  # 5 seconds timeout
                if response.status_code == 200:
                    logging.info("Rust server started successfully.")
                    return rust_process
                else:
                    logging.error(f"Unexpected response from server: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {str(e)}")
                retries -= 1
                time.sleep(2)

        logging.error("Failed to start Rust backend server after multiple attempts.")
        messagebox.showerror("Backend Server Error", "Failed to start the Rust backend server.")
        raise Exception("Rust backend server not responsive after retries")
        
    except Exception as e:
        logging.error("Failed to start Rust backend server.", exc_info=True)
        messagebox.showerror("Backend Server Error", "Failed to start the Rust backend server.")
        raise e


def main():
    """
    Main entry point for the Advanced Downloader application.
    Initializes the Tkinter root window and starts the GUI.
    """
    try:
        logging.info("Starting Advanced Downloader application.")
        rust_process = run_rust_backend()  # Start Rust server in the background

        # Now initialize and run the Python GUI
        root = tk.Tk()
        app = DownloaderApp(root)

        # Handle application close to terminate Rust backend process
        def on_close():
            try:
                logging.info("Closing application.")
                rust_process.terminate()  # Terminate Rust backend process
                root.destroy()
            except Exception as e:
                logging.error("Failed to terminate Rust process.", exc_info=True)

        root.protocol("WM_DELETE_WINDOW", on_close)
        
        root.mainloop()
        logging.info("Application closed successfully.")  # ✅ Log exit

    except Exception as e:
        logging.error("An error occurred while running the application.", exc_info=True)

        # ✅ User-Friendly Error Message
        user_message = (
            "Oops! Something went wrong.\n"
            "Please restart the application.\n\n"
            "If the issue persists, check 'app.log' for details."
        )

        messagebox.showerror("Application Error", user_message)
        print(f"An error occurred while running the application: {e}")


if __name__ == "__main__":
    main()
