"""Aba de atividades gerais."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from datetime import datetime

from ..models import (
    GeneralEvent,
    EventHistoryEntry,
    FinalizedEventBatch,
    FinalizedEventBatchEntry,
)
from ..utils import normalize_date
from .widgets import DateEntryFrame, TimeEntryFrame
from .dialogs import AddEventDialog


class EventsTab(ttk.Frame):
    """Aba de gerenciamento de atividades."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._current_event: Optional[GeneralEvent] = None
        self._acolyte_vars: dict = {}
        self._auto_save_enabled = True
        self._build()

    def _build(self):
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Painel esquerdo: lista de atividades ---
        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=240)

        ttk.Button(left, text="➕ Adicionar Atividade", command=self._add_event).pack(
            fill=tk.X, pady=4
        )

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.event_listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE
        )
        self.event_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.event_listbox.yview)
        self.event_listbox.bind("<<ListboxSelect>>", self._on_event_select)

        ttk.Button(left, text="🗑️ Remover Atividade", command=self._remove_event).pack(
            fill=tk.X, pady=4
        )

        ttk.Button(
            left,
            text="✅ Registrar Atividades",
            command=self._finalize_events,
        ).pack(fill=tk.X, pady=4)

        # --- Painel direito: detalhes da atividade ---
        self.right = ttk.Frame(paned, padding=4)
        paned.add(self.right, minsize=400)
        self._build_event_detail()

    def _build_event_detail(self):
        self.detail_label = ttk.Label(
            self.right, text="Selecione uma atividade para editar.", foreground="gray"
        )
        self.detail_label.pack(pady=20)

        self.detail_frame = ttk.Frame(self.right)

        fields = ttk.Frame(self.detail_frame)
        fields.pack(fill=tk.X)

        ttk.Label(fields, text="Nome:").grid(row=0, column=0, sticky="w", pady=4)
        self.ev_name_var = tk.StringVar()
        self.ev_name_var.trace_add("write", lambda *args: self._auto_save_event())
        ttk.Entry(fields, textvariable=self.ev_name_var, width=28).grid(
            row=0, column=1, padx=6, pady=4
        )

        ttk.Label(fields, text="Data (DD/MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.ev_date_var = tk.StringVar()
        self.ev_date_var.trace_add("write", lambda *args: self._auto_save_event())
        DateEntryFrame(fields, textvariable=self.ev_date_var, width=8, date_format="DD/MM").grid(
            row=1, column=1, padx=6, pady=4, sticky="w"
        )

        ttk.Label(fields, text="Horário:").grid(row=2, column=0, sticky="w", pady=4)
        self.ev_time_var = tk.StringVar()
        self.ev_time_var.trace_add("write", lambda *args: self._auto_save_event())
        TimeEntryFrame(fields, textvariable=self.ev_time_var, width=10).grid(
            row=2, column=1, padx=6, pady=4, sticky="w"
        )

        ttk.Label(
            self.detail_frame, text="Participantes:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(8, 2))

        part_scroll_frame = ttk.Frame(self.detail_frame)
        part_scroll_frame.pack(fill=tk.BOTH, expand=True)

        part_canvas = tk.Canvas(part_scroll_frame, height=200, highlightthickness=0)
        part_vscroll = ttk.Scrollbar(
            part_scroll_frame, orient=tk.VERTICAL, command=part_canvas.yview
        )
        part_canvas.configure(yscrollcommand=part_vscroll.set)
        part_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        part_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.participants_inner = ttk.Frame(part_canvas)
        self.participants_window = part_canvas.create_window(
            (0, 0), window=self.participants_inner, anchor="nw"
        )

        def on_configure(event):
            part_canvas.configure(scrollregion=part_canvas.bbox("all"))

        self.participants_inner.bind("<Configure>", on_configure)

        ttk.Button(
            self.detail_frame, text="💾 Salvar Atividade", command=self._save_event
        ).pack(fill=tk.X, pady=8)

    def _show_detail(self):
        self.detail_label.pack_forget()
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    def _hide_detail(self):
        self.detail_frame.pack_forget()
        self.detail_label.pack(pady=20)

    def refresh_list(self):
        self.event_listbox.delete(0, tk.END)
        for ev in self.app.general_events:
            time_str = f" {ev.time}" if ev.time else ""
            self.event_listbox.insert(tk.END, f"{ev.name} - {ev.date}{time_str}")

    def _on_event_select(self, event=None):
        sel = self.event_listbox.curselection()
        if not sel:
            self._hide_detail()
            self._current_event = None
            return
        idx = sel[0]
        if idx < len(self.app.general_events):
            self._current_event = self.app.general_events[idx]
            self._load_event_detail()
            self._show_detail()

    def _load_event_detail(self):
        ev = self._current_event
        if not ev:
            return
        self._auto_save_enabled = False
        self.ev_name_var.set(ev.name)
        self.ev_date_var.set(ev.date)
        self.ev_time_var.set(ev.time)
        self._rebuild_participants()
        self._auto_save_enabled = True

    def _rebuild_participants(self):
        for widget in self.participants_inner.winfo_children():
            widget.destroy()
        self._acolyte_vars.clear()

        ev = self._current_event
        if not ev:
            return
        sorted_acolytes = sorted(self.app.acolytes, key=lambda a: a.name)
        for ac in sorted_acolytes:
            var = tk.BooleanVar(value=ac.id not in ev.excluded_acolyte_ids)
            var.trace_add("write", lambda *args: self._auto_save_event())
            self._acolyte_vars[ac.id] = var
            ttk.Checkbutton(
                self.participants_inner, text=ac.name, variable=var
            ).pack(anchor="w", padx=4)

    def _auto_save_event(self):
        if not self._auto_save_enabled or not self._current_event:
            return
        ev = self._current_event
        ev.name = self.ev_name_var.get().strip()
        ev.date = normalize_date(self.ev_date_var.get().strip())
        ev.time = self.ev_time_var.get().strip()

        ev.excluded_acolyte_ids = [
            aid for aid, var in self._acolyte_vars.items() if not var.get()
        ]
        self.refresh_list()
        self.app.save()

    def _save_event(self):
        self._auto_save_event()
        if self._current_event:
            messagebox.showinfo("Salvo", "Atividade salva com sucesso!")

    def _add_event(self):
        dlg = AddEventDialog(self.app.root)
        if dlg.result:
            name, date, time = dlg.result
            ev = GeneralEvent(id=str(uuid.uuid4()), name=name, date=date, time=time)
            self.app.general_events.append(ev)
            self.refresh_list()
            self.app.save()

    def _remove_event(self):
        sel = self.event_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma atividade para remover.")
            return
        idx = sel[0]
        if idx >= len(self.app.general_events):
            return
        ev = self.app.general_events[idx]
        if not messagebox.askyesno("Confirmar", f"Remover atividade '{ev.name}'?"):
            return
        self.app.general_events.pop(idx)
        self._current_event = None
        self._hide_detail()
        self.refresh_list()
        self.app.save()

    def _finalize_events(self):
        if not self.app.general_events:
            messagebox.showinfo("Aviso", "Nenhuma atividade cadastrada.")
            return
        if not messagebox.askyesno(
            "Confirmar",
            "Deseja registrar todas as atividades? "
            "As atividades serão contabilizadas e removidas da aba.",
        ):
            return
        batch_id = str(uuid.uuid4())
        entries = []
        count = 0
        for ev in self.app.general_events:
            participants = [
                ac.id for ac in self.app.acolytes if ac.id not in ev.excluded_acolyte_ids
            ]
            entry = FinalizedEventBatchEntry(
                event_id=ev.id,
                name=ev.name,
                date=ev.date,
                time=ev.time,
                participating_acolyte_ids=participants,
            )
            entries.append(entry)
            for ac in self.app.acolytes:
                if ac.id not in ev.excluded_acolyte_ids:
                    hist_entry = EventHistoryEntry(
                        event_id=ev.id,
                        name=ev.name,
                        date=ev.date,
                        time=ev.time,
                    )
                    ac.event_history.append(hist_entry)
                    count += 1
        batch = FinalizedEventBatch(
            id=batch_id,
            finalized_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            entries=entries,
        )
        self.app.finalized_event_batches.append(batch)
        self.app.general_events.clear()
        self._current_event = None
        self._hide_detail()
        self.refresh_list()
        self.app.save()
        if hasattr(self.app, 'history_tab'):
            self.app.history_tab.refresh()
        messagebox.showinfo(
            "Concluído", f"Atividades registradas! {count} registros adicionados."
        )
