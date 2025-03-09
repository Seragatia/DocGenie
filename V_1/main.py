import tkinter as tk
from tkinter import messagebox
import logging
from gui.main_window import DownloaderApp

# ✅ Improved Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    filename="app.log",
    filemode="a",  # Append to log file
)


def main():
    """
    Main entry point for the Advanced Downloader application.
    Initializes the Tkinter root window and starts the GUI.
    """
    try:
        logging.info("Starting Advanced Downloader application.")
        root = tk.Tk()
        app = DownloaderApp(root)
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
