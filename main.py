import tkinter as tk
from tkinter import messagebox
import logging
from gui.main_window import DownloaderApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",  # Append to the log file
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
    except Exception as e:
        logging.error("An error occurred while running the application.", exc_info=True)
        messagebox.showerror("Application Error", f"An unexpected error occurred:\n{e}")
        print(f"An error occurred while running the application: {e}")

if __name__ == "__main__":
    main()
