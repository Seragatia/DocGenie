# gui/dialogs/auth_dialog.py
import tkinter as tk
from tkinter import ttk, StringVar, BooleanVar, messagebox
from typing import Optional, Dict, Any
import logging

from gui.utils.helpers import validate_url

class AuthorizationDialog(tk.Toplevel):
    """
    Dialog for user authentication before downloading,
    using dynamic light/dark themes.
    """

    _active_dialog = None

    def __init__(self, parent: tk.Tk, url: str = "", theme: Optional[Dict[str, str]] = None) -> None:
        logging.debug("Initializing AuthorizationDialog with URL: %s", url)

        # Prevent multiple dialogs
        if AuthorizationDialog._active_dialog:
            AuthorizationDialog._active_dialog.lift()
            AuthorizationDialog._active_dialog.focus_force()
            return
        AuthorizationDialog._active_dialog = self

        super().__init__(parent)
        self.parent = parent
        self.result: Optional[Dict[str, Any]] = None
        self.theme = theme or {}

        self.title("Authorization Required")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.geometry("420x240")
        self.resizable(False, False)

        # Variables
        self.url_var = StringVar(self, value=url)
        self.username_var = StringVar(self)
        self.password_var = StringVar(self)
        self.use_auth_var = BooleanVar(self, value=False)

        # Build the UI
        self._create_widgets()

        # Apply theme & center
        self._apply_theme()
        self._center_dialog()

        # Key bindings
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        logging.debug("AuthorizationDialog initialized successfully")

    def _create_widgets(self) -> None:
        """Create and layout widgets inside the dialog."""
        logging.debug("Creating widgets in AuthorizationDialog")

        # Main container with 2 columns
        self.container = ttk.Frame(self, padding=15)
        self.container.pack(fill="both", expand=True)

        # Column 1 can expand
        self.container.columnconfigure(1, weight=1)

        # Row 0: Address label + combobox
        self.address_label = ttk.Label(self.container, text="Address:")
        self.address_label.grid(row=0, column=0, sticky="e", padx=(0, 8), pady=(0, 8))

        self.url_entry = ttk.Combobox(
            self.container,
            textvariable=self.url_var,
            width=30
        )
        self.url_entry.grid(row=0, column=1, sticky="we", pady=(0, 8))
        self.url_entry.bind("<FocusOut>", self.validate_url)

        # Row 1: Checkbutton
        self.auth_checkbox = ttk.Checkbutton(
            self.container,
            text="Use authorization",
            variable=self.use_auth_var,
            command=self.toggle_auth
        )
        self.auth_checkbox.grid(row=1, column=1, sticky="w", pady=(0, 8))

        # Row 2: Username
        self.username_label = ttk.Label(self.container, text="Username:")
        self.username_label.grid(row=2, column=0, sticky="e", padx=(0, 8), pady=4)

        self.username_entry = ttk.Entry(
            self.container,
            textvariable=self.username_var,
            width=20,
            state="disabled"
        )
        self.username_entry.grid(row=2, column=1, sticky="we", pady=4)

        # Row 3: Password
        self.password_label = ttk.Label(self.container, text="Password:")
        self.password_label.grid(row=3, column=0, sticky="e", padx=(0, 8), pady=4)

        self.password_entry = ttk.Entry(
            self.container,
            textvariable=self.password_var,
            width=20,
            show="*",
            state="disabled"
        )
        self.password_entry.grid(row=3, column=1, sticky="we", pady=4)

        # Row 4: Buttons in column=1, aligned right
        btn_frame = ttk.Frame(self.container, style="AuthDialog.TFrame")
        btn_frame.grid(row=4, column=1, sticky="e", pady=(10, 0))

        self.cancel_button = ttk.Button(
            btn_frame, text="Cancel", command=self.on_cancel, width=10,
            style="AuthDialog.TButton"
        )
        self.cancel_button.pack(side="left", padx=(0, 10))

        self.ok_button = ttk.Button(
            btn_frame, text="OK", command=self.on_ok, width=10,
            style="AuthDialog.TButton"
        )
        self.ok_button.pack(side="left")

    def toggle_auth(self) -> None:
        """Enable or disable username & password fields based on checkbox state."""
        state = "normal" if self.use_auth_var.get() else "disabled"
        self.username_entry.config(state=state)
        self.password_entry.config(state=state)

    def validate_url(self, event=None) -> bool:
        """Validate the entered URL and show warning if invalid."""
        url = self.url_var.get().strip()
        if not validate_url(url):
            messagebox.showwarning("Invalid URL", "⚠ Invalid URL! Must start with http:// or https://")
            self.url_entry.focus_set()
            return False
        return True

    def on_ok(self) -> None:
        """Confirm authentication details and close the dialog."""
        if not self.validate_url():
            logging.warning("Invalid URL entered in AuthorizationDialog")
            return

        self.result = {
            "use_authorization": self.use_auth_var.get(),
            "url": self.url_var.get().strip(),
            "username": self.username_var.get().strip() if self.use_auth_var.get() else "",
            "password": self.password_var.get().strip() if self.use_auth_var.get() else "",
        }
        logging.info("AuthorizationDialog result: %s", self.result)
        self._close_dialog()

    def on_cancel(self) -> None:
        """Cancel authentication and close the dialog."""
        logging.info("AuthorizationDialog canceled by user")
        self.result = None
        self._close_dialog()

    def _close_dialog(self) -> None:
        """Close dialog and restore focus to parent."""
        if AuthorizationDialog._active_dialog is not self:
            return
        AuthorizationDialog._active_dialog = None
        self.grab_release()
        self.destroy()
        self.parent.focus_force()

    def _center_dialog(self) -> None:
        """Center dialog over the parent window."""
        self.update_idletasks()
        x = self.parent.winfo_rootx() + self.parent.winfo_width() // 2 - self.winfo_width() // 2
        y = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _apply_theme(self) -> None:
        """
        (Re)Apply the theme to all widgets.
        Called during init or whenever we want to refresh theme.
        """
        bg        = self.theme.get("dialog_bg", self.theme.get("bg", "#ffffff"))
        fg        = self.theme.get("dialog_fg", self.theme.get("fg", "#000000"))
        btn_bg    = self.theme.get("button_bg", "#e0e0e0")
        btn_fg    = self.theme.get("button_fg", "#000000")
        check_bg  = self.theme.get("check_bg", bg)
        check_fg  = self.theme.get("check_fg", fg)
        combo_bg  = self.theme.get("combobox_bg", self.theme.get("entry_bg", "#ffffff"))
        combo_fg  = self.theme.get("combobox_fg", self.theme.get("entry_fg", "#000000"))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("AuthDialog.TFrame", background=bg)
        style.configure("AuthDialog.TLabel", background=bg, foreground=fg)
        style.configure("AuthDialog.TButton", background=btn_bg, foreground=btn_fg)
        style.configure("AuthDialog.TCheckbutton", background=check_bg, foreground=check_fg)
        style.configure(
            "AuthDialog.TEntry",
            fieldbackground=self.theme.get("entry_bg", "#ffffff"),
            foreground=self.theme.get("entry_fg", "#000000")
        )
        style.configure(
            "AuthDialog.TCombobox",
            fieldbackground=combo_bg,
            foreground=combo_fg
        )
        style.map("AuthDialog.TCombobox",
                  fieldbackground=[("readonly", combo_bg)],
                  foreground=[("readonly", combo_fg)])

        # Reassign style to each widget in the container
        for child in self.container.winfo_children():
            cls = child.winfo_class()
            if cls in ("TLabel", "Label"):
                child.configure(style="AuthDialog.TLabel")
            elif cls in ("TEntry", "Entry"):
                child.configure(style="AuthDialog.TEntry")
            elif cls in ("TCombobox", "Combobox"):
                child.configure(style="AuthDialog.TCombobox")
            elif cls in ("TCheckbutton", "Checkbutton"):
                child.configure(style="AuthDialog.TCheckbutton")
            elif cls in ("TButton", "Button"):
                child.configure(style="AuthDialog.TButton")

        self.container.configure(style="AuthDialog.TFrame")
        self.configure(bg=bg)
        self.update_idletasks()

    def refresh_theme(self, new_theme: Dict[str, str]) -> None:
        """Public method to re-apply a new theme dictionary while the dialog is still open."""
        self.theme = new_theme
        self._apply_theme()
