import tkinter as tk

def make_table_scrollable(canvas, frame):
    """
    Enables scrolling for a frame inside a canvas.
    Args:
        canvas (tk.Canvas): The canvas wrapping the frame.
        frame (tk.Frame): The inner frame inside the canvas.
    """

    def on_frame_configure(event):
        """Updates the scroll region to allow scrolling beyond the visible area."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_mouse_wheel(event):
        """Enables scrolling with the mouse wheel."""
        if event.state & 1:  # Shift key is held down for horizontal scrolling
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<MouseWheel>", on_mouse_wheel)

    # Attach frame to canvas
    canvas.create_window((0, 0), window=frame, anchor="nw")
