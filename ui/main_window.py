import tkinter as tk
from tkinter import ttk

from data.storage import load_data, save_data
from ui.schedule_tab import ScheduleTab
from ui.events_tab import EventsTab
from ui.acolytes_tab import AcolytesTab


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Acólitos")
        self.minsize(1200, 700)
        self.geometry("1200x700")

        self.acolytes, self.slots, self.events = load_data()

        self._build()

    def _build(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self._schedule_tab = ScheduleTab(self._notebook, self)
        self._events_tab = EventsTab(self._notebook, self)
        self._acolytes_tab = AcolytesTab(self._notebook, self)

        self._notebook.add(self._schedule_tab, text="  Escala  ")
        self._notebook.add(self._events_tab, text="  Eventos  ")
        self._notebook.add(self._acolytes_tab, text="  Acólitos  ")

        self._schedule_tab.refresh()
        self._events_tab.refresh()
        self._acolytes_tab.refresh()

    def save(self):
        save_data(self.acolytes, self.slots, self.events)

    def on_acolytes_changed(self):
        """Called when the acolyte list is modified so other tabs can update."""
        self._schedule_tab.refresh()
        self._events_tab.refresh()
