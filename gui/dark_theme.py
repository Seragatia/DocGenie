import tkinter as tk
from tkinter import ttk

def apply_dark_theme(root):
    """
    Applies a dark theme to the entire Tkinter application.
    Args:
        root (tk.Tk): The root Tkinter window.
    """
    dark_bg = "#1E1E1E"
    light_fg = "#FFFFFF"
    accent_color = "#2D2D2D"
    highlight_color = "#3E3E3E"
    
    # Set the main window background color
    root.configure(bg=dark_bg)

    # Configure styles for buttons, labels, and entry fields
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("TFrame", background=dark_bg)
    style.configure("TLabel", background=dark_bg, foreground=light_fg, font=("Arial", 10))
    style.configure("TButton", background=accent_color, foreground=light_fg, borderwidth=1)
    style.map("TButton", background=[("active", highlight_color)])
    
    style.configure("TEntry", fieldbackground=accent_color, foreground=light_fg, borderwidth=1)
    style.configure("Treeview", background=dark_bg, foreground=light_fg, fieldbackground=dark_bg, rowheight=25)
    style.configure("Treeview.Heading", background=highlight_color, foreground=light_fg, font=("Arial", 11, "bold"))

    # Set scrollbar colors
    style.configure("Vertical.TScrollbar", background=accent_color)
    style.configure("Horizontal.TScrollbar", background=accent_color)
    
    # Ensure all widgets follow the theme
    for widget in root.winfo_children():
        widget.configure(bg=dark_bg)
