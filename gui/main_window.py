import tkinter as tk
from tkinter import Toplevel, StringVar, Entry, Label, Button, Checkbutton, IntVar
from gui.toolbar import create_toolbar
from gui.url_input import URLInput
from gui.download_table import DownloadTable
from gui.menu_bar import MenuBar
from gui.status_label import StatusLabel
from modules.download_logic import DownloadLogic
from modules.add_url_logic import AddURLLogic


class DownloaderApp:
    def __init__(self, root):
        """
        Initialize the main downloader application window.
        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.root.title("Advanced Downloader")
        self.root.geometry("900x500")
        self.root.resizable(True, True)

        # Initialize Logic Modules
        self.download_logic = DownloadLogic(self)
        self.add_url_logic = AddURLLogic(self)

        # Create GUI Components
        self.menu_bar = MenuBar(root, self)  # Menu Bar
        create_toolbar(root, self)          # Toolbar
        self.url_input = URLInput(root, self)  # URL Input Section
        self.download_table = DownloadTable(root)  # Download Table
        self.status_label = StatusLabel(root)  # Status Label

    def show_add_url_window(self):
        """
        Displays a new window for entering a download URL.
        """
        # Create a new top-level window
        add_url_window = Toplevel(self.root)
        add_url_window.title("Enter new address to download")
        add_url_window.geometry("400x200")
        add_url_window.resizable(False, False)

        # Initialize variables to store input values
        url_var = StringVar()
        use_auth_var = IntVar()
        login_var = StringVar()
        password_var = StringVar()

        # Create and place widgets in the window
        Label(add_url_window, text="Address:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        Entry(add_url_window, textvariable=url_var, width=40).grid(row=0, column=1, padx=10, pady=5)

        Checkbutton(add_url_window, text="Use authorization", variable=use_auth_var).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )

        Label(add_url_window, text="Login:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        Entry(add_url_window, textvariable=login_var, width=25).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        Label(add_url_window, text="Password:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        Entry(add_url_window, textvariable=password_var, width=25, show="*").grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # OK and Cancel Buttons
        Button(
            add_url_window,
            text="OK",
            command=lambda: self.add_url_logic.process_url(
                add_url_window, url_var.get(), use_auth_var.get(), login_var.get(), password_var.get()
            ),
        ).grid(row=4, column=0, padx=10, pady=10)

        Button(add_url_window, text="Cancel", command=add_url_window.destroy).grid(row=4, column=1, padx=10, pady=10)

    def update_status(self, message, color="blue"):
        """
        Updates the status message displayed in the status label.
        Args:
            message (str): The status message to display.
            color (str): The color of the status text.
        """
        self.status_label.update_status(message, color)
def show_download_info_window(self, url, file_path, category="General", description=""):
    """
    Displays the Download File Info dialog and starts downloading the file.
    Args:
        url (str): The URL of the file to be downloaded.
        file_path (str): The default save path for the file.
        category (str): The category for the download.
        description (str): Description of the download.
    """
    download_info_window = Toplevel(self.root)
    download_info_window.title("Download File Info")
    download_info_window.geometry("600x400")
    download_info_window.resizable(False, False)

    # Variables to store input values
    category_var = StringVar(value=category)
    file_path_var = StringVar(value=file_path)
    description_var = StringVar(value=description)

    # URL Display
    Label(download_info_window, text="URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    Entry(download_info_window, text=url, state="readonly", width=50).grid(row=0, column=1, padx=10, pady=5)

    # Category Input
    Label(download_info_window, text="Category:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    Entry(download_info_window, textvariable=category_var, width=25).grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # Save Path Input
    Label(download_info_window, text="Save As:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    Entry(download_info_window, textvariable=file_path_var, width=50).grid(row=2, column=1, padx=10, pady=5)

    # Description Input
    Label(download_info_window, text="Description:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    Entry(download_info_window, textvariable=description_var, width=50).grid(row=3, column=1, padx=10, pady=5)

    # Download Buttons
    Button(
        download_info_window,
        text="Start Download",
        command=lambda: self.start_download_and_close(
            download_info_window, url, file_path_var.get(), category_var.get(), description_var.get()
        ),
    ).grid(row=4, column=0, padx=10, pady=10)

    Button(download_info_window, text="Cancel", command=download_info_window.destroy).grid(row=4, column=1, padx=10, pady=10)


def start_download_and_close(self, window, url, file_path, category, description):
    """
    Handles the download logic and closes the dialog window.
    Args:
        window (Toplevel): The "Download File Info" dialog.
        url (str): The URL to be downloaded.
        file_path (str): The file save path.
        category (str): The download category.
        description (str): The download description.
    """
    try:
        self.download_logic.start_download_with_details(url, file_path, category, description)
        self.update_status("Download started successfully.", "green")
        window.destroy()
    except Exception as e:
        self.update_status(f"Error: {e}", "red")
