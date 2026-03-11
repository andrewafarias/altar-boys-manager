"""Gerenciamento inline de atividades gerais."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from datetime import datetime

from ..models import GeneralEvent, EventHistoryEntry, FinalizedEventBatch, FinalizedEventBatchEntry
from ..utils import normalize_date, detect_weekday, next_occurrence_of_day
from .widgets import DateEntryFrame, TimeEntryFrame
from .dialogs import AddEventDialog, EditEventParticipantsDialog


def _time_in_interval(time_str: str, start_time: str, end_time: str) -> bool:
    """Returns True if time_str falls within [start_time, end_time)."""
    try:
        from datetime import datetime as _dt
        t = _dt.strptime(time_str, "%H:%M").time()
        s = _dt.strptime(start_time, "%H:%M").time()
        e = _dt.strptime(end_time, "%H:%M").time()
        return s <= t < e
    except (ValueError, AttributeError):
        return False


class EventCard(ttk.LabelFrame):
    """Card inline para edição de uma atividade pendente."""

    def __init__(self, parent, event: GeneralEvent, app, schedule_tab, on_remove: Callable[[GeneralEvent], None]):
        super().__init__(parent, text=f"Atividade #{event.id[:6]}", padding=6)
        self.app = app
        self.event = event
        self.schedule_tab = schedule_tab
        self._on_remove = on_remove
        self._build()
        self._refresh_participants_summary()

    def _build(self):
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=2)

        # Bind drag events to the card and its frames
        self.schedule_tab._bind_drag_to_widget(self, "event", self.event.id)
        self.schedule_tab._bind_drag_to_widget(row1, "event", self.event.id, card=self)

        ttk.Label(row1, text="Nome:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.event.name)
        self.name_var.trace_add("write", self._on_field_change)
        ttk.Entry(row1, textvariable=self.name_var, width=24).pack(side=tk.LEFT, padx=4)

        ttk.Label(row1, text="Data:").pack(side=tk.LEFT, padx=(8, 0))
        self.date_var = tk.StringVar(value=self.event.date)
        self.date_var.trace_add("write", self._on_field_change)
        DateEntryFrame(row1, textvariable=self.date_var, width=8, date_format="DD/MM").pack(side=tk.LEFT, padx=4)

        ttk.Label(row1, text="Hora:").pack(side=tk.LEFT, padx=(8, 0))
        self.time_var = tk.StringVar(value=self.event.time)
        self.time_var.trace_add("write", self._on_field_change)
        TimeEntryFrame(row1, textvariable=self.time_var, width=8).pack(side=tk.LEFT, padx=4)

        ttk.Button(row1, text="✕", width=3, command=self._remove_self).pack(side=tk.RIGHT)

        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=(4, 2))

        ttk.Button(row2, text="✏️ Editar Acólitos Incluídos", command=self._edit_included_acolytes).pack(side=tk.LEFT)

        self.include_in_message_var = tk.BooleanVar(value=self.event.include_in_message)
        self.include_in_message_var.trace_add("write", self._on_include_in_message_change)
        ttk.Checkbutton(row2, text="Incluir na mensagem", variable=self.include_in_message_var).pack(side=tk.LEFT, padx=(8, 0))

        self.summary_var = tk.StringVar()
        ttk.Label(row2, textvariable=self.summary_var, foreground="#1f4f7a").pack(side=tk.LEFT, padx=10)

        # Bind drag to row2
        self.schedule_tab._bind_drag_to_widget(row2, "event", self.event.id, card=self)

    def _included_acolyte_ids(self):
        excluded = set(self.event.excluded_acolyte_ids)
        return [ac.id for ac in self.app.acolytes if ac.id not in excluded]

    def _refresh_participants_summary(self):
        included_names = [ac.name for ac in self.app.acolytes if ac.id not in self.event.excluded_acolyte_ids]
        if not included_names:
            self.summary_var.set("Nenhum acólito incluído")
            return
        preview = ", ".join(included_names[:4])
        if len(included_names) > 4:
            preview = f"{preview}... (+{len(included_names) - 4})"
        self.summary_var.set(f"Incluídos: {len(included_names)} | {preview}")

    def _on_field_change(self, *_):
        self.event.name = self.name_var.get().strip()
        self.event.date = normalize_date(self.date_var.get().strip())
        self.event.time = self.time_var.get().strip()
        self._check_unavailability_on_edit()
        self.app.save()
        # Check if ordering changed when date/time updates
        self.schedule_tab._check_and_refresh_if_ordering_changed()

    def _check_unavailability_on_edit(self):
        """Check if included acolytes are unavailable with the current date/time."""
        day = detect_weekday(self.event.date)
        time = self.event.time
        if not day or not time:
            return
        included_ids = self._included_acolyte_ids()
        if not included_ids:
            return
        conflict_warnings = []
        for aid in included_ids:
            acolyte = self.app.find_acolyte(aid)
            if acolyte and hasattr(acolyte, 'unavailabilities'):
                for unav in acolyte.unavailabilities:
                    if unav.day == day and _time_in_interval(time, unav.start_time, unav.end_time):
                        conflict_warnings.append(
                            f"{acolyte.name}: indisponível às {time} "
                            f"({unav.start_time}–{unav.end_time})"
                        )
                        break
        if conflict_warnings:
            from tkinter import messagebox
            messagebox.showwarning(
                "Aviso de Indisponibilidade",
                "Os seguintes acólitos têm indisponibilidade no novo horário:\n\n"
                + "\n".join(conflict_warnings),
                parent=self,
            )

    def _on_include_in_message_change(self, *_):
        self.event.include_in_message = bool(self.include_in_message_var.get())
        self.app.save()

    def _edit_included_acolytes(self):
        dlg = EditEventParticipantsDialog(self.app.root, self.app.acolytes, self._included_acolyte_ids())
        if dlg.result is None:
            return
        selected_ids = set(dlg.result)
        self.event.excluded_acolyte_ids = [ac.id for ac in self.app.acolytes if ac.id not in selected_ids]
        self._refresh_participants_summary()
        self.app.save()

    def _remove_self(self):
        self._on_remove(self.event)


class EventsTab:
    """Gerenciador inline de atividades pendentes."""

    def __init__(self, app, schedule_tab):
        self.app = app
        self.schedule_tab = schedule_tab

    def create_card(self, parent, event: GeneralEvent):
        return EventCard(parent, event, self.app, self.schedule_tab, self._remove_event)

    def refresh_list(self):
        self.schedule_tab.refresh_cards()

    def add_event(self):
        dlg = AddEventDialog(self.app.root)
        if dlg.result:
            name, date, time = dlg.result
            ev = GeneralEvent(
                id=str(uuid.uuid4()),
                name=name,
                date=date,
                time=time,
                order_index=self.schedule_tab.next_card_order_index(),
            )
            self.app.general_events.append(ev)
            self.schedule_tab.refresh_cards()
            self.app.save()

    def _remove_event(self, ev: GeneralEvent):
        if not messagebox.askyesno("Confirmar", f"Remover atividade '{ev.name}'?"):
            return
        self.app.general_events = [item for item in self.app.general_events if item.id != ev.id]
        self.schedule_tab.refresh_cards()
        self.app.save()

    def finalize_pending_events(self) -> int:
        if not self.app.general_events:
            return 0

        batch_id = str(uuid.uuid4())
        entries = []
        count = 0
        regenerated_events = []

        for ev in self.app.general_events:
            participants = [ac.id for ac in self.app.acolytes if ac.id not in ev.excluded_acolyte_ids]
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
                    hist_entry = EventHistoryEntry(event_id=ev.id, name=ev.name, date=ev.date, time=ev.time)
                    ac.event_history.append(hist_entry)
                    count += 1

            weekday = detect_weekday(ev.date)
            next_date = next_occurrence_of_day(weekday) if weekday else ev.date
            regenerated_events.append(
                GeneralEvent(
                    id=str(uuid.uuid4()),
                    name=ev.name,
                    date=next_date,
                    time=ev.time,
                    include_in_message=ev.include_in_message,
                    excluded_acolyte_ids=list(ev.excluded_acolyte_ids),
                    order_index=ev.order_index,
                )
            )

        batch = FinalizedEventBatch(
            id=batch_id,
            finalized_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            entries=entries,
        )
        self.app.finalized_event_batches.append(batch)
        self.app.general_events = regenerated_events
        self.schedule_tab.refresh_cards()
        return count
