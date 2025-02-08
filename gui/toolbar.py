import tkinter as tk

def create_toolbar(root, app):
    toolbar = tk.Frame(root, bg="lightgrey", relief=tk.RAISED, bd=2)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    tk.Button(toolbar, text="Add URL", command=app.download_logic.start_download).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(toolbar, text="Resume", command=app.download_logic.resume_download).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(toolbar, text="Stop", command=app.download_logic.stop_download).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(toolbar, text="Stop All", command=app.download_logic.stop_all_downloads).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(toolbar, text="Delete", command=app.download_logic.delete_selected).pack(side=tk.LEFT, padx=5, pady=2)
