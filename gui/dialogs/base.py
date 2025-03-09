# gui/dialogs/base.py

import tkinter as tk
from typing import Optional, Dict
import logging

class ModalDialog:
    """
    Base class for modal dialogs that enforce modal behavior and temporarily disable
    UI interactions on the parent. Only one ModalDialog can be active at a time.
    """

    _active_dialog = None  # Track the currently active modal dialog

    def __init__(self, parent: tk.Toplevel, theme: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize the ModalDialog with a given parent and optional theme.

        - If there's already an active modal dialog, it brings that dialog to the front
          and returns immediately, skipping further initialization of a second dialog.
        - Otherwise, creates a tk.Toplevel as the dialog window, disables the parent's menu (if any),
          and centers the dialog.

        Args:
            parent (tk.Toplevel): The parent window or toplevel.
            theme (Optional[Dict[str, str]]): A dictionary containing theme properties.
        """
        logging.debug("Initializing ModalDialog")

        # Prevent multiple dialogs from opening
        if ModalDialog._active_dialog:
            logging.debug("An active ModalDialog already exists. Bringing it to the front.")
            ModalDialog._active_dialog.dialog.lift()
            ModalDialog._active_dialog.dialog.focus_force()
            return

        # Mark this as the active dialog
        ModalDialog._active_dialog = self

        self.parent = parent
        self.theme = theme or {}
        self._old_menu_states = {}
        self._after_ids = {}  # store any scheduled after() IDs for later cancellation

        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.transient(parent)      # Keep it on top of parent
        self.dialog.grab_set()             # Redirect events to this dialog
        self.dialog.protocol("WM_DELETE_WINDOW", self._close_dialog)
        self.dialog.focus_set()
        self.dialog.lift()
        self.dialog.configure(bg=self.theme.get("dialog_bg", self.theme.get("bg", "white")))

        # Disable parent's menu items (if any)
        self._disable_menu()

        # Immediately center the dialog over the parent
        self.parent.update_idletasks()
        self.dialog.update_idletasks()
        self._center_dialog()

        logging.debug("ModalDialog initialized successfully")

    def _disable_menu(self) -> None:
        """
        Disable all menu items in the parent window if a menu is present.
        Stores original states in _old_menu_states for later restoration.
        """
        try:
            menu = self.parent.cget("menu")
            if not menu or not isinstance(menu, tk.Menu):
                logging.debug("Parent has no valid menu to disable.")
                return

            num_entries = menu.index("end")
            if num_entries is None:
                logging.debug("Parent menu has no entries to disable.")
                return

            for i in range(num_entries + 1):
                try:
                    state = menu.entrycget(i, "state")
                    self._old_menu_states[i] = state
                    menu.entryconfig(i, state="disabled")
                    logging.debug(f"Disabled menu item {i}.")
                except tk.TclError:
                    logging.warning(f"Could not disable menu item {i}. It may not exist.")
        except tk.TclError:
            logging.warning("No valid menu or entries found to disable.")

    def _enable_menu(self) -> None:
        """
        Restore the parent's menu items to their original states,
        using the data in _old_menu_states.
        """
        try:
            menu = self.parent.cget("menu")
            if menu and self._old_menu_states:
                for index, state in self._old_menu_states.items():
                    try:
                        menu.entryconfig(index, state=state)
                        logging.debug(f"Restored menu item {index} to state: {state}")
                    except tk.TclError:
                        logging.warning(f"Could not restore menu item {index}. It may no longer exist.")
        except tk.TclError:
            logging.warning("Unable to restore menu items.")

    def _center_dialog(self) -> None:
        """
        Center the dialog over its parent. If an error occurs,
        logs the exception but continues execution.
        """
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
        """
        Properly close the dialog, cancelling any scheduled 'after' events,
        re-enabling the parent's menu, and destroying the toplevel.
        """
        if ModalDialog._active_dialog is not self:
            logging.debug("Close request ignored: this is not the active dialog.")
            return

        logging.debug("Closing ModalDialog")

        # Cancel any pending tk.after() events
        for after_id in self._after_ids.values():
            try:
                self.dialog.after_cancel(after_id)
                logging.debug(f"Cancelled scheduled after event: {after_id}")
            except Exception as exc:
                logging.debug(f"Error cancelling after event {after_id}: {exc}")

        ModalDialog._active_dialog = None
        self._enable_menu()
        self.dialog.destroy()

        # Restore focus to parent
        self.parent.update_idletasks()
        self.parent.lift()
        self.parent.focus_force()
        logging.debug("ModalDialog closed successfully.")
