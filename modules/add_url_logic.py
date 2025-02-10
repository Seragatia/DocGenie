import os
from tkinter import Toplevel, StringVar, Entry, Label, Button, Checkbutton, IntVar, filedialog, OptionMenu

class AddURLLogic:
    """
    Logic to process and validate user input from the Add URL and Download File Info windows.
    """

    def __init__(self, app):
        """
        Args:
            app: Reference to the main application instance.
        """
        self.app = app

    def process_url(self, window, url, use_auth, login, password):
        """
        Processes the URL input from the Add URL window.
        Args:
            window (Toplevel): The Add URL window.
            url (str): The URL entered by the user.
            use_auth (bool): Whether to use authentication.
            login (str): The login username.
            password (str): The login password.
        """
        try:
            if not url:
                self.app.update_status("Error: URL is required!", "red")
                return

            if use_auth and (not login or not password):
                self.app.update_status("Error: Login and password are required for authentication.", "red")
                return

            # Show the Download File Info dialog
            self.show_download_file_info(url)
            
            # Close the Add URL window
            window.destroy()

        except Exception as e:
            self.app.update_status(f"Unexpected error: {e}", "red")

    def show_download_file_info(self, url):
        """
        Displays the "Download File Info" dialog for entering download details.
        Args:
            url (str): The URL to download.
        """
        dialog = Toplevel(self.app.root)
        dialog.title("Download File Info")
        dialog.geometry("500x300")
        dialog.resizable(False, False)

        # Variables
        category_var = StringVar(value="General")
        file_path_var = StringVar(value=os.path.join("Downloads", os.path.basename(url)))
        description_var = StringVar()

        # URL Field
        Label(dialog, text="URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        Entry(dialog, state="readonly", textvariable=StringVar(value=url), width=60).grid(row=0, column=1, padx=10, pady=5)

        # Category Field
        Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        category_menu = OptionMenu(dialog, category_var, "General", "Videos", "Documents", "Music", "Other")
        category_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Save-As Field
        Label(dialog, text="Save As:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        Entry(dialog, textvariable=file_path_var, width=60).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        Button(dialog, text="...", command=lambda: self.select_file(file_path_var)).grid(row=2, column=2, padx=5, pady=5)

        # Description Field
        Label(dialog, text="Description:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        Entry(dialog, textvariable=description_var, width=60).grid(row=3, column=1, padx=10, pady=5)

        # Buttons
        Button(dialog, text="Download Later", command=dialog.destroy).grid(row=4, column=0, padx=10, pady=20, sticky="w")
        Button(
            dialog,
            text="Start Download",
            command=lambda: self.start_download_with_details(
                url, file_path_var.get(), category_var.get(), description_var.get(), dialog
            ),
        ).grid(row=4, column=1, padx=10, pady=20, sticky="e")
        Button(dialog, text="Cancel", command=dialog.destroy).grid(row=4, column=2, padx=10, pady=20)

    def select_file(self, file_path_var):
        """
        Opens a file dialog to select a save-as path.
        Args:
            file_path_var (StringVar): The variable holding the save-as file path.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".html")
        if file_path:
            file_path_var.set(file_path)

    def start_download_with_details(self, url, file_path, category, description, dialog):
        """
        Starts a download with detailed information.
        Args:
            url (str): The URL to download.
            file_path (str): The path to save the file.
            category (str): The selected category.
            description (str): Description for the download.
            dialog (Toplevel): The dialog window to close.
        """
        try:
            if not url or not file_path:
                raise ValueError("URL and file path are required.")

            # Start the download using the DownloadLogic module
            self.app.download_logic.start_download_with_details(url, file_path, category, description)
            self.app.update_status(f"Started downloading: {url}", "green")
            dialog.destroy()
        except ValueError as ve:
            self.app.update_status(f"Error: {ve}", "red")
        except Exception as e:
            self.app.update_status(f"Unexpected Error: {e}", "red")
