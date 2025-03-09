# gui/dialogs/base.py
import tkinter as tk
from typing import Optional, Dict
import logging

class ModalDialog:
    """Base class for modal dialogs that enforce modal behavior and temporarily disable UI interactions."""
    _active_dialog = None  # Track active dialog to prevent multiple openings

    def __init__(self, parent: tk.Toplevel, theme: Optional[Dict[str, str]] = None) -> None:
        logging.debug("Initializing ModalDialog")

        # Prevent multiple dialogs from opening
        if ModalDialog._active_dialog:
            logging.debug("An active dialog already exists. Bringing it to front.")
            ModalDialog._active_dialog.dialog.lift()
            ModalDialog._active_dialog.dialog.focus_force()
            return  

        ModalDialog._active_dialog = self  # Set this as the active dialog
        self.parent = parent
        self.theme = theme or {}
        self._old_menu_states = {}
        self._after_ids = {}  # Dictionary to store any scheduled after() IDs

        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self._close_dialog)
        self.dialog.focus_set()
        self.dialog.lift()
        self.dialog.configure(bg=self.theme.get("dialog_bg", self.theme.get("bg", "white")))

        # Disable parent's menu items (if any)
        self._disable_menu()

        # Immediately center the dialog
        self.parent.update_idletasks()
        self.dialog.update_idletasks()
        self._center_dialog()

        logging.debug("ModalDialog initialized successfully")

    def _disable_menu(self) -> None:
        try:
            menu = self.parent.cget("menu")
            if not menu or not isinstance(menu, tk.Menu):
                return
            num_entries = menu.index("end")
            if num_entries is None:
                return
            for i in range(num_entries + 1):
                try:
                    state = menu.entrycget(i, "state")
                    self._old_menu_states[i] = state
                    menu.entryconfig(i, state="disabled")
                except tk.TclError:
                    logging.warning(f"Could not disable menu item {i}.")
        except tk.TclError:
            logging.warning("No valid menu entries found to disable.")

    def _enable_menu(self) -> None:
        try:
            menu = self.parent.cget("menu")
            if menu and self._old_menu_states:
                for index, state in self._old_menu_states.items():
                    try:
                        menu.entryconfig(index, state=state)
                    except tk.TclError:
                        logging.warning(f"Could not restore menu item {index}.")
        except tk.TclError:
            logging.warning("Unable to restore menu items.")

    def _center_dialog(self) -> None:
        try:
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            dw = self.dialog.winfo_width()
            dh = self.dialog.winfo_height()
            x = max(px + (pw // 2) - (dw // 2), 0)
            y = max(py + (ph // 2) - (dh // 2), 0)
            self.dialog.geometry(f"+{x}+{y}")
            logging.debug(f"Dialog centered at: {x}, {y}")
        except Exception as e:
            logging.error(f"Error centering dialog: {e}")

    def _close_dialog(self) -> None:
        if ModalDialog._active_dialog is not self:
            return
        logging.debug("Closing ModalDialog")
        # Cancel any pending after events
        for after_id in self._after_ids.values():
            try:
                self.dialog.after_cancel(after_id)
            except Exception:
                pass
        ModalDialog._active_dialog = None
        self._enable_menu()
        self.dialog.destroy()
        self.parent.update_idletasks()
        self.parent.lift()
        self.parent.focus_force()
        logging.debug("ModalDialog closed successfully")
