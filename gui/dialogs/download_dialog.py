# gui/dialogs/download_dialog.py

import tkinter as tk
from tkinter import ttk, StringVar, BooleanVar, filedialog
from typing import Optional, Dict, Any
import logging

from gui.dialogs.base import ModalDialog
from gui.utils.helpers import validate_url

DEFAULT_CATEGORY_PATHS: Dict[str, str] = {
    "General": "Downloads",
    "Video": "/Users/yourusername/Videos",
    "Music": "/Users/yourusername/Music",
    "Documents": "/Users/yourusername/Documents",
}

class DownloadOptionsDialog(ModalDialog):
    """
    Dialog for selecting download options (category, path, etc.).
    Inherits from ModalDialog to provide modal behavior and theming.
    """
    _active_dialog = None  # Track any currently open instance.

    def __init__(
        self,
        parent: tk.Widget,
        url: str = "",
        file_size_kb: int = 0,
        theme: Optional[Dict[str, str]] = None
    ) -> None:
        logging.debug(f"Initializing DownloadOptionsDialog with URL: {url}")

        # Ensure only one DownloadOptionsDialog exists at a time.
        if DownloadOptionsDialog._active_dialog:
            logging.debug("An existing DownloadOptionsDialog is active. Destroying it.")
            DownloadOptionsDialog._active_dialog.dialog.destroy()
            DownloadOptionsDialog._active_dialog = None

        DownloadOptionsDialog._active_dialog = self
        super().__init__(parent, theme)

        self.result: Optional[Dict[str, Any]] = None
        self.theme = theme or {}
        self._processing = False
        # Dictionary to store any scheduled tk 'after' events if we need to cancel them.
        self._after_ids: Dict[str, str] = {}

        # Hide the dialog until theme is applied and geometry is computed.
        self.dialog.withdraw()

        self.dialog.title("Download Options")
        self.dialog.resizable(False, False)

        # Set up local style context and use "clam".
        self.style = ttk.Style(self.dialog)
        self.style.theme_use("clam")

        # Variables bound to widgets
        self.url_var = StringVar(self.dialog, value=url)
        self.category_var = StringVar(self.dialog, value="General")
        self.save_path_var = StringVar(self.dialog, value=DEFAULT_CATEGORY_PATHS["General"])
        self.remember_path_var = BooleanVar(self.dialog, value=False)
        self.file_size_kb = file_size_kb
        self.description_var = StringVar(self.dialog)

        # Build and lay out widgets
        self._create_widgets()

        # Apply theme
        self.apply_theme()

        # Update geometry and center
        self.dialog.update()
        self._center_dialog()

        # Schedule deiconify so user won't see the dialog in an unstyled state.
        deiconify_id = self.dialog.after(0, self.dialog.deiconify)
        self._after_ids["deiconify"] = deiconify_id

        logging.debug("DownloadOptionsDialog initialized successfully")

    def apply_theme(self) -> None:
        """Applies the current theme styling to this dialog's widgets."""
        if not self.theme:
            return

        self.style.theme_use("clam")

        # Extract or fallback to theme colors
        let_bg   = self.theme.get("dialog_bg", self.theme.get("bg", "#1E1E1E"))
        let_fg   = self.theme.get("dialog_fg", self.theme.get("fg", "#FFFFFF"))
        entry_bg = self.theme.get("dialog_entry_bg", self.theme.get("entry_bg", "#2A2A2A"))
        entry_fg = self.theme.get("dialog_entry_fg", self.theme.get("entry_fg", "#D0D0D0"))
        btn_bg   = self.theme.get("dialog_button_bg", self.theme.get("button_bg", "#3E3E3E"))
        btn_fg   = self.theme.get("button_fg", "#FFFFFF")
        combo_bg = self.theme.get("combobox_bg", "#2A2A2A")
        combo_fg = self.theme.get("combobox_fg", "#D0D0D0")
        chk_fg   = self.theme.get("check_fg", self.theme.get("fg", "#FFFFFF"))

        # Dialog background
        self.dialog.configure(bg=let_bg)

        # Basic styles for TFrame, TLabel, TEntry, TCombobox, TButton, TCheckbutton
        self.style.configure("DownloadDialog.TFrame",
            background=let_bg, borderwidth=0, relief="flat"
        )
        self.style.configure("DownloadDialog.TLabel",
            background=let_bg, foreground=let_fg
        )
        self.style.configure("DownloadDialog.TEntry",
            fieldbackground=entry_bg, foreground=entry_fg,
            borderwidth=0, relief="flat"
        )
        self.style.configure("DownloadDialog.TCombobox",
            fieldbackground=combo_bg, foreground=combo_fg,
            borderwidth=0, relief="flat"
        )
        self.style.map("DownloadDialog.TCombobox",
            fieldbackground=[("readonly", combo_bg)],
            foreground=[("readonly", combo_fg)]
        )
        self.style.configure("DownloadDialog.TButton",
            background=btn_bg, foreground=btn_fg,
            borderwidth=0, relief="flat"
        )
        self.style.configure("DownloadDialog.TCheckbutton",
            background=let_bg, foreground=chk_fg,
            indicatoron=True, borderwidth=0, relief="flat"
        )
        self.style.map("DownloadDialog.TCheckbutton",
            background=[("active", let_bg), ("selected", let_bg)],
            foreground=[("active", chk_fg), ("selected", chk_fg)]
        )
        self.style.configure("Error.TLabel",
            background=let_bg, foreground="red",
            borderwidth=0, relief="flat"
        )

        self.container.configure(bg=let_bg, bd=0, highlightthickness=0, relief="flat")
        self.dialog.update()

    def refresh_theme(self, new_theme: Dict[str, str]) -> None:
        """Re-apply a new theme dictionary while the dialog is still open."""
        logging.debug("Refreshing theme in DownloadOptionsDialog.")
        self.theme = new_theme
        self.apply_theme()

    def _create_widgets(self) -> None:
        logging.debug("Creating widgets in DownloadOptionsDialog")

        self.container = tk.Frame(self.dialog, bd=0, highlightthickness=0, relief="flat")
        self.container.pack(padx=8, pady=8)

        # Row 0: URL label + entry
        ttk.Label(self.container, text="URL:", style="DownloadDialog.TLabel")\
            .grid(row=0, column=0, sticky="e", padx=(0,5), pady=(0,5))
        self.url_entry = ttk.Entry(
            self.container,
            textvariable=self.url_var,
            width=35,
            style="DownloadDialog.TEntry"
        )
        self.url_entry.grid(row=0, column=1, sticky="we", padx=(0,5), pady=(0,5))
        self.url_entry.bind("<FocusOut>", self._validate_url)

        # Row 1: Error label
        self.error_label = ttk.Label(self.container, text="", style="Error.TLabel")
        self.error_label.grid(row=1, column=1, sticky="w", padx=(0,5), pady=(0,5))

        # Row 2: Category label + combobox
        ttk.Label(self.container, text="Category:", style="DownloadDialog.TLabel")\
            .grid(row=2, column=0, sticky="e", padx=(0,5), pady=(0,5))
        self.category_box = ttk.Combobox(
            self.container,
            textvariable=self.category_var,
            values=list(DEFAULT_CATEGORY_PATHS.keys()),
            state="readonly",
            style="DownloadDialog.TCombobox",
            width=33
        )
        self.category_box.grid(row=2, column=1, sticky="we", padx=(0,5), pady=(0,5))
        self.category_box.bind("<<ComboboxSelected>>", self.on_category_change)

        # Row 3: Save As label + entry + browse button
        ttk.Label(self.container, text="Save As:", style="DownloadDialog.TLabel")\
            .grid(row=3, column=0, sticky="e", padx=(0,5), pady=(0,5))
        self.save_path_entry = ttk.Entry(
            self.container,
            textvariable=self.save_path_var,
            width=35,
            style="DownloadDialog.TEntry"
        )
        self.save_path_entry.grid(row=3, column=1, sticky="we", padx=(0,5), pady=(0,5))

        browse_btn = ttk.Button(
            self.container,
            text="Browse",
            command=self.browse_save_path,
            style="DownloadDialog.TButton",
            width=8
        )
        browse_btn.grid(row=3, column=2, padx=(0,0), pady=(0,5))

        # Row 4: "Remember Path" checkbutton
        self.remember_cb = ttk.Checkbutton(
            self.container,
            text="Remember this path",
            variable=self.remember_path_var,
            style="DownloadDialog.TCheckbutton"
        )
        self.remember_cb.grid(row=4, column=1, sticky="w", padx=(0,5), pady=(0,5))

        # Row 5: Description label + entry
        ttk.Label(self.container, text="Description:", style="DownloadDialog.TLabel")\
            .grid(row=5, column=0, sticky="e", padx=(0,5), pady=(0,5))
        self.description_entry = ttk.Entry(
            self.container,
            textvariable=self.description_var,
            width=35,
            style="DownloadDialog.TEntry"
        )
        self.description_entry.grid(row=5, column=1, sticky="we", padx=(0,5), pady=(0,5))

        # Separator
        sep = ttk.Separator(self.container, orient="horizontal")
        sep.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8,5))

        # Row 7: Button frame
        btn_frame = ttk.Frame(self.container, style="DownloadDialog.TFrame")
        btn_frame.grid(row=7, column=0, columnspan=3, sticky="ew")

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
            style="DownloadDialog.TButton",
            width=8
        )
        self.cancel_btn.pack(side="left", padx=(0,5))

        self.later_btn = ttk.Button(
            btn_frame,
            text="Download Later",
            command=lambda: self.on_ok("download_later"),
            style="DownloadDialog.TButton",
            width=14
        )
        self.later_btn.pack(side="left", padx=(0,5))

        self.start_btn = ttk.Button(
            btn_frame,
            text="Start Now",
            command=lambda: self.on_ok("start_now"),
            style="DownloadDialog.TButton",
            width=10
        )
        self.start_btn.pack(side="left", padx=(0,5))

        self.container.columnconfigure(1, weight=1)

    def on_ok(self, action: str) -> None:
        """User confirmed the dialog (start now or download later)."""
        if self._processing:
            logging.debug("Dialog is already processing a request, ignoring duplicate on_ok call.")
            return
        self._processing = True

        # Disable buttons to prevent duplicates
        self.start_btn.config(state="disabled")
        self.later_btn.config(state="disabled")
        self.cancel_btn.config(state="disabled")

        if not self._validate_url():
            # Re-enable if validation failed
            self.start_btn.config(state="normal")
            self.later_btn.config(state="normal")
            self.cancel_btn.config(state="normal")
            self._processing = False
            return

        # Build the result dictionary
        self.result = {
            "url": self.url_var.get().strip(),
            "category": self.category_var.get().strip(),
            "save_path": self.save_path_var.get().strip(),
            "remember_path": self.remember_path_var.get(),
            "file_size_kb": self.file_size_kb,
            "description": self.description_var.get().strip(),
            "action": action,
        }

        logging.debug(f"Dialog confirmed with result: {self.result}")
        self._close_dialog()

    def on_cancel(self) -> None:
        """User canceled the dialog."""
        logging.debug("Dialog canceled by user.")
        self.result = None
        self._close_dialog()

    def browse_save_path(self) -> None:
        """Open a directory chooser to set the save path."""
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)
            logging.debug(f"User selected directory: {path}")

    def on_category_change(self, event=None) -> None:
        """Updates the save path if the category changed and 'Remember path' is not checked."""
        category = self.category_var.get().strip()
        if category in DEFAULT_CATEGORY_PATHS and not self.remember_path_var.get():
            self.save_path_var.set(DEFAULT_CATEGORY_PATHS[category])
            logging.debug(f"Category changed to {category}, updated save path to {DEFAULT_CATEGORY_PATHS[category]}")

    def _validate_url(self, event=None) -> bool:
        """Check that the URL is valid and display an error if not."""
        url = self.url_var.get().strip()
        if not validate_url(url):
            self.error_label.config(text="⚠ Invalid URL! Must start with http:// or https://")
            self.url_entry.focus_set()
            logging.warning(f"User entered an invalid URL: {url}")
            return False
        self.error_label.config(text="")
        return True
