import logging
from tkinter import ttk
from typing import Optional, Any, List, Tuple

# Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class TableUtils:
    """
    Manages and updates the download table in the UI.
    """

    def __init__(self, tree: ttk.Treeview) -> None:
        """
        Initialize the TableUtils with the given treeview widget.
        
        Args:
            tree (ttk.Treeview): The table widget for displaying downloads.
        """
        self.tree = tree

    def add_row(
        self,
        file_name: str,
        size: str,
        progress: str,
        status: str,
        time_left: str,
        transfer_rate: str,
        date_added: str,
        file_type: str = "",
        resolution: str = "",
        download_path: str = "",
        source_url: str = "",
    ) -> Optional[str]:
        """
        Adds a new row to the download table.
        
        Args:
            file_name (str): The name of the file.
            size (str): The file size.
            progress (str): The download progress (e.g., percentage).
            status (str): The current status of the download.
            time_left (str): Estimated time remaining.
            transfer_rate (str): Current download speed.
            date_added (str): Date when the download was added.
            file_type (str): The file type (optional).
            resolution (str): The resolution (optional).
            download_path (str): The file path where it is saved (optional).
            source_url (str): The original download URL (optional).

        Returns:
            Optional[str]: The ID of the newly inserted item in the table, or None if a duplicate exists.
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
                    file_type,
                    resolution,
                    download_path,
                    source_url,
                ),
            )
            return item_id
        except Exception as e:
            logging.error(f"Error adding row to table: {e}")
            return None

    def update_progress(self, item_id: str, **kwargs: Any) -> None:
        """
        Updates the progress and status of a download in the table.
        
        Args:
            item_id (str): The ID of the row to update.
            **kwargs: Column values to update. Valid keys include any table column.
        """
        try:
            if not self.tree.exists(item_id):
                logging.error(f"Attempted to update a non-existent item: {item_id}")
                return

            values: List[Any] = list(self.tree.item(item_id, "values"))

            column_map = {col: idx for idx, col in enumerate([
                "File Name", "Size", "Progress", "Status", "Time Left", "Transfer Rate",
                "Date Added", "File Type", "Resolution", "Download Path", "Source URL"
            ])}

            for key, value in kwargs.items():
                if key in column_map:
                    values[column_map[key]] = value

            self.tree.item(item_id, values=values)
        except Exception as e:
            logging.error(f"Error updating table row {item_id}: {e}")

    def get_selected_downloads(self) -> List[Tuple[Any, ...]]:
        """
        Retrieves all selected downloads (for batch operations).

        Returns:
            List[Tuple[Any, ...]]: A list of tuples containing the values of selected rows.
        """
        try:
            return [self.tree.item(item, "values") for item in self.tree.selection()]
        except Exception as e:
            logging.error(f"Error retrieving selected downloads: {e}")
            return []

    def delete_selected(self) -> None:
        """
        Deletes the selected downloads from the table.
        """
        try:
            for item in self.tree.selection():
                self.tree.delete(item)
        except Exception as e:
            logging.error(f"Error deleting selected downloads: {e}")

    def clear_all(self) -> None:
        """
        Clears all downloads from the table.
        """
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
        except Exception as e:
            logging.error(f"Error clearing download table: {e}")

    def file_exists(self, file_name: str) -> bool:
        """
        Checks if a file already exists in the download table.

        Args:
            file_name (str): The name of the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            return any(
                self.tree.item(item, "values")[0] == file_name for item in self.tree.get_children()
            )
        except Exception as e:
            logging.error(f"Error checking file existence: {e}")
            return False
