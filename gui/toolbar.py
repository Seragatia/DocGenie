import tkinter as tk
from modules.toolbar_logic import ToolbarLogic

def create_toolbar(root, app):
    """
    Creates a toolbar with buttons.
    Args:
        root: The root Tkinter container.
        app: The main application instance.
    """
    # Initialize Toolbar Logic
    toolbar_logic = ToolbarLogic(app)

    # Create Toolbar Frame
    toolbar = tk.Frame(root, bg="lightgrey", relief=tk.RAISED, bd=2)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # Add Toolbar Buttons
    tk.Button(
        toolbar,
        text="Add URL",
        command=toolbar_logic.add_url  # Use logic from ToolbarLogic
    ).pack(side=tk.LEFT, padx=5, pady=2)

    tk.Button(
        toolbar,
        text="Start Download",
        command=lambda: app.show_download_file_info_window("URL_HERE")  # Placeholder logic for starting downloads
    ).pack(side=tk.LEFT, padx=5, pady=2)

    tk.Button(
        toolbar,
        text="Resume",
        command=toolbar_logic.resume_download  # Use logic from ToolbarLogic
    ).pack(side=tk.LEFT, padx=5, pady=2)

    tk.Button(
        toolbar,
        text="Stop",
        command=toolbar_logic.stop_download  # Use logic from ToolbarLogic
    ).pack(side=tk.LEFT, padx=5, pady=2)

    tk.Button(
        toolbar,
        text="Stop All",
        command=toolbar_logic.stop_all_downloads  # Use logic from ToolbarLogic
    ).pack(side=tk.LEFT, padx=5, pady=2)

    tk.Button(
        toolbar,
        text="Delete",
        command=toolbar_logic.delete_selected  # Use logic from ToolbarLogic
    ).pack(side=tk.LEFT, padx=5, pady=2)
