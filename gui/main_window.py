import tkinter as tk
from gui.toolbar import create_toolbar
from gui.url_input import URLInput
from gui.download_table import DownloadTable
from gui.menu_bar import MenuBar
from gui.status_label import StatusLabel
from modules.download_logic import DownloadLogic

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Downloader")
        self.root.geometry("900x500")
        self.root.resizable(True, True)

        # Download Logic (Initialize First)
        self.download_logic = DownloadLogic(self)

        # Menu Bar
        self.menu_bar = MenuBar(root, self)

        # Toolbar
        create_toolbar(root, self)

        # Input Section
        self.url_input = URLInput(root, self)

        # Download Table
        self.download_table = DownloadTable(root)

        # Status Label
        self.status_label = StatusLabel(root)

    def update_status(self, message, color="blue"):
        self.status_label.update_status(message, color)
