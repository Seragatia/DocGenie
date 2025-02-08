import tkinter as tk
from gui.main_window import DownloaderApp

def main():
    """
    Main entry point for the Advanced Downloader application.
    Initializes the Tkinter root window and starts the GUI.
    """
    try:
        root = tk.Tk()
        app = DownloaderApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred while running the application: {e}")

if __name__ == "__main__":
    main()
