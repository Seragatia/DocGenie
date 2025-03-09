# table_utils.py
import logging
from tkinter import ttk

# ✅ Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class TableUtils:
    """
    ✅ Manages and updates the download table in the UI.
    """

    def __init__(self, tree):
        """
        Args:
            tree (ttk.Treeview): The table widget for displaying downloads.
        """
        self.tree = tree

    def add_row(
        self, file_name, size, progress, status, time_left, transfer_rate, date_added
    ):
        """
        ✅ Adds a new row to the download table.

        Args:
            file_name (str): The name of the file.
            size (str): The file size.
            progress (str): The download progress percentage.
            status (str): The current status of the download.
            time_left (str): Estimated time remaining.
            transfer_rate (str): Download speed.
            date_added (str): Date when the download was added.

        Returns:
            str: The ID of the newly inserted item in the table.
        """
        try:
            if self.file_exists(file_name):
                logging.warning(f"Duplicate entry prevented: {file_name}")
                return None

            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    file_name,
                    size,
                    progress,
                    status,
                    time_left,
                    transfer_rate,
                    date_added,
                ),
            )
            return item_id
        except Exception as e:
            logging.error(f"Error adding row to table: {e}")
            return None

    def update_progress(self, item_id, **kwargs):
        """
        ✅ Updates the progress and status of a download in the table.

        Args:
            item_id (str): The ID of the row to update.
            **kwargs: The column values to update.
        """
        try:
            if not self.tree.exists(item_id):
                logging.error(f"Attempted to update a non-existent item: {item_id}")
                return

            values = list(self.tree.item(item_id, "values"))

            # ✅ Mapping table columns to indices
            column_map = {
                "file_name": 0,
                "size": 1,
                "progress": 2,
                "status": 3,
                "time_left": 4,
                "transfer_rate": 5,
                "date_added": 6,
            }

            for key, value in kwargs.items():
                if key in column_map:
                    values[column_map[key]] = value

            self.tree.item(item_id, values=values)

        except Exception as e:
            logging.error(f"Error updating table row {item_id}: {e}")

    def get_selected_download(self):
        """
        ✅ Retrieves the selected download from the table.

        Returns:
            tuple: The selected row values or None if nothing is selected.
        """
        try:
            selected_item = self.tree.selection()
            if selected_item:
                return self.tree.item(selected_item[0], "values")
            return None
        except Exception as e:
            logging.error(f"Error retrieving selected download: {e}")
            return None

    def get_selected_downloads(self):
        """
        ✅ Retrieves all selected downloads (for batch operations).

        Returns:
            list: A list of tuples containing selected row values.
        """
        try:
            selected_items = self.tree.selection()
            return (
                [self.tree.item(item, "values") for item in selected_items]
                if selected_items
                else []
            )
        except Exception as e:
            logging.error(f"Error retrieving selected downloads: {e}")
            return []

    def delete_selected(self):
        """
        ✅ Deletes the selected download from the table.
        """
        try:
            selected_item = self.tree.selection()
            if selected_item:
                self.tree.delete(selected_item)
        except Exception as e:
            logging.error(f"Error deleting selected download: {e}")

    def delete_multiple(self):
        """
        ✅ Deletes multiple selected downloads from the table.
        """
        try:
            selected_items = self.tree.selection()
            for item in selected_items:
                self.tree.delete(item)
        except Exception as e:
            logging.error(f"Error deleting multiple downloads: {e}")

    def clear_all(self):
        """
        ✅ Clears all downloads from the table.
        """
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
        except Exception as e:
            logging.error(f"Error clearing download table: {e}")

    def file_exists(self, file_name):
        """
        ✅ Checks if a file already exists in the download table.

        Args:
            file_name (str): The name of the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[0] == file_name:
                    return True
            return False
        except Exception as e:
            logging.error(f"Error checking file existence: {e}")
            return False
