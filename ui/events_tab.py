import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List

from models.models import GeneralEvent, HistoryEntry


class NewEventDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Evento Geral")
        self.resizable(False, False)
        self.result = None
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky="w", **pad)
        self._date = ttk.Entry(self, width=16)
        self._date.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Hora (HH:MM, opcional):").grid(row=1, column=0, sticky="w", **pad)
        self._time = ttk.Entry(self, width=10)
        self._time.grid(row=1, column=1, **pad)

        ttk.Label(self, text="Descrição:").grid(row=2, column=0, sticky="w", **pad)
        self._desc = ttk.Entry(self, width=30)
        self._desc.grid(row=2, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        date = self._date.get().strip()
        time = self._time.get().strip()
        desc = self._desc.get().strip()
        if not date:
            messagebox.showerror("Erro", "A data é obrigatória.", parent=self)
            return
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.", parent=self)
            return
        if time:
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                messagebox.showerror("Erro", "Hora inválida. Use HH:MM.", parent=self)
                return
        if not desc:
            messagebox.showerror("Erro", "A descrição é obrigatória.", parent=self)
            return
        self.result = (date, time, desc)
        self.destroy()


class ExcludeAcolytesDialog(tk.Toplevel):
    def __init__(self, parent, event: GeneralEvent, acolytes):
        super().__init__(parent)
        self.title("Excluir Acólitos do Evento")
        self.geometry("360x400")
        self._event = event
        self._acolytes = acolytes
        self._vars = {}
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        ttk.Label(self, text="Desmarque os acólitos que NÃO participaram:",
                  wraplength=340).pack(padx=10, pady=8)

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10)
        canvas = tk.Canvas(frame, highlightthickness=0)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for acolyte in self._acolytes:
            var = tk.BooleanVar(value=(acolyte.id not in self._event.excluded_acolyte_ids))
            self._vars[acolyte.id] = var
            ttk.Checkbutton(inner, text=acolyte.name, variable=var).pack(anchor="w", pady=1)

        ttk.Button(self, text="Salvar", command=self._save).pack(pady=8)

    def _save(self):
        self._event.excluded_acolyte_ids = [
            aid for aid, var in self._vars.items() if not var.get()
        ]
        self.destroy()


class EventsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Form area
        form = ttk.LabelFrame(self, text="Novo Evento Geral", padding=8)
        form.grid(row=0, column=0, sticky="ew", padx=8, pady=6)

        ttk.Button(form, text="+ Adicionar Evento", command=self._add_event).pack(anchor="w")

        # Events list
        list_frame = ttk.LabelFrame(self, text="Eventos Cadastrados", padding=4)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.grid(row=0, column=0, sticky="nsew")

        self._events_container = ttk.Frame(canvas)
        self._canvas_window = canvas.create_window((0, 0), window=self._events_container, anchor="nw")
        self._events_container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._canvas_window, width=e.width))
        self._canvas = canvas

    def refresh(self):
        self._refresh_events()

    def _refresh_events(self):
        for w in self._events_container.winfo_children():
            w.destroy()
        for event in self._app.events:
            self._build_event_card(event)

    def _build_event_card(self, event: GeneralEvent):
        registered_color = "#d4edda" if event.registered else "#fff3cd"
        card = ttk.LabelFrame(self._events_container, padding=6)
        card.pack(fill="x", padx=6, pady=4)

        header = ttk.Frame(card)
        header.pack(fill="x")

        time_str = f" - {event.time}" if event.time else ""
        status_label = " ✓ Registrado" if event.registered else ""
        title = f"{event.date}{time_str} | {event.description}{status_label}"
        ttk.Label(header, text=title, font=("", 10, "bold")).pack(side="left")
        ttk.Button(header, text="✕", width=3,
                   command=lambda e=event: self._delete_event(e)).pack(side="right")

        excluded_count = len(event.excluded_acolyte_ids)
        info = f"Excluídos: {excluded_count} acólito(s)"
        ttk.Label(card, text=info, foreground="gray").pack(anchor="w")

        btn_row = ttk.Frame(card)
        btn_row.pack(anchor="w", pady=(4, 0))
        ttk.Button(btn_row, text="Gerenciar Excluídos",
                   command=lambda e=event: self._manage_excluded(e)).pack(side="left", padx=2)
        if not event.registered:
            ttk.Button(btn_row, text="Registrar Participação",
                       command=lambda e=event: self._register_event(e)).pack(side="left", padx=2)

    def _add_event(self):
        dialog = NewEventDialog(self)
        if dialog.result:
            date, time, desc = dialog.result
            event = GeneralEvent(date=date, time=time, description=desc)
            self._app.events.append(event)
            self._app.save()
            self._refresh_events()

    def _delete_event(self, event: GeneralEvent):
        if not messagebox.askyesno("Confirmar", f"Excluir o evento '{event.description}'?"):
            return
        self._app.events = [e for e in self._app.events if e.id != event.id]
        self._app.save()
        self._refresh_events()

    def _manage_excluded(self, event: GeneralEvent):
        ExcludeAcolytesDialog(self, event, self._app.acolytes)
        self._app.save()
        self._refresh_events()

    def _register_event(self, event: GeneralEvent):
        if not messagebox.askyesno(
            "Confirmar",
            f"Registrar participação no evento '{event.description}' ({event.date})?\n"
            "Isso contabilizará a participação de todos os acólitos não excluídos."
        ):
            return
        for acolyte in self._app.acolytes:
            if acolyte.id not in event.excluded_acolyte_ids:
                acolyte.history.append(HistoryEntry(
                    date=event.date,
                    time=event.time,
                    description=event.description,
                    entry_type="evento",
                ))
        event.registered = True
        self._app.save()
        self._refresh_events()
        messagebox.showinfo("Registrado", "Participação no evento registrada com sucesso!")
