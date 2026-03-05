"""Classe base para diálogos modais."""

import tkinter as tk


class BaseDialog(tk.Toplevel):
    """Base para diálogos modais."""

    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._center()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _ok(self):
        raise NotImplementedError

    def _cancel(self):
        self.result = None
        self.destroy()
