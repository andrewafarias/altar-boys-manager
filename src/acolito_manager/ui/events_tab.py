"""Gerenciamento inline de atividades gerais."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from datetime import datetime

from ..models import GeneralEvent, EventHistoryEntry, FinalizedEventBatch, FinalizedEventBatchEntry
from ..utils import WEEKDAYS_PT, normalize_date, detect_weekday, next_occurrence_of_day
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


def _is_temp_unav_conflict(slot_date: str, slot_time: str, temp_unav) -> bool:
    """Returns True if slot_date/slot_time conflicts with a TemporaryUnavailability."""
    if not slot_date:
        return False
    try:
        from datetime import datetime as _dt

        d = _dt.strptime(slot_date, "%d/%m/%Y").date()
        start_d = _dt.strptime(temp_unav.start_date, "%d/%m/%Y").date()
        end_d = _dt.strptime(temp_unav.end_date, "%d/%m/%Y").date()
        if not (start_d <= d <= end_d):
            return False
    except (ValueError, AttributeError):
        return False

    if not temp_unav.start_time or not temp_unav.end_time:
        return True
    if not slot_time:
        return True
    return _time_in_interval(slot_time, temp_unav.start_time, temp_unav.end_time)


def _acolyte_unavailability_reason(acolyte, slot_date: str, slot_day: str, slot_time: str) -> str:
    """Return a human-readable conflict reason or an empty string when available."""
    if slot_day and slot_time:
        for unav in getattr(acolyte, "unavailabilities", []):
            if unav.day == slot_day and _time_in_interval(slot_time, unav.start_time, unav.end_time):
                return f"indisponível às {slot_time} ({unav.start_time}-{unav.end_time})"

    for temp_unav in getattr(acolyte, "temporary_unavailabilities", []):
        if _is_temp_unav_conflict(slot_date, slot_time, temp_unav):
            time_info = (
                f"{temp_unav.start_time}-{temp_unav.end_time}"
                if temp_unav.start_time and temp_unav.end_time
                else "dia todo"
            )
            return f"indisponibilidade temporária em {slot_date} ({time_info})"

    return ""


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
        self._updating_fields = False

        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Nome:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.event.name)
        self.name_var.trace_add("write", self._on_field_change)
        ttk.Entry(row1, textvariable=self.name_var, width=24).pack(side=tk.LEFT, padx=4)

        ttk.Label(row1, text="Data:").pack(side=tk.LEFT, padx=(8, 0))
        self.date_var = tk.StringVar(value=self.event.date)
        self.date_var.trace_add("write", self._on_date_change)
        DateEntryFrame(row1, textvariable=self.date_var, width=8, date_format="DD/MM").pack(side=tk.LEFT, padx=4)

        ttk.Label(row1, text="Hora:").pack(side=tk.LEFT, padx=(8, 0))
        self.time_var = tk.StringVar(value=self.event.time)
        self.time_var.trace_add("write", self._on_field_change)
        TimeEntryFrame(row1, textvariable=self.time_var, width=8).pack(side=tk.LEFT, padx=4)

        ttk.Button(row1, text="✕", width=3, command=self._remove_self).pack(side=tk.RIGHT)

        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=(4, 2))

        ttk.Label(row2, text="Dia:").pack(side=tk.LEFT)
        default_day = detect_weekday(self.event.date) or WEEKDAYS_PT[datetime.now().weekday()]
        self.day_var = tk.StringVar(value=default_day)
        self.day_combo = ttk.Combobox(
            row2,
            textvariable=self.day_var,
            values=WEEKDAYS_PT,
            width=16,
            state="readonly",
        )
        self.day_combo.pack(side=tk.LEFT, padx=4)
        self.day_var.trace_add("write", self._on_day_change)

        row3 = ttk.Frame(self)
        row3.pack(fill=tk.X, pady=(2, 2))

        self.participants_frame = ttk.Frame(row3)
        self.participants_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row4 = ttk.Frame(self)
        row4.pack(fill=tk.X, pady=(2, 0))

        ttk.Button(row4, text="✏️ Editar Excluídos", command=self._edit_included_acolytes).pack(side=tk.LEFT)

        self.include_in_message_var = tk.BooleanVar(value=self.event.include_in_message)
        self.include_in_message_var.trace_add("write", self._on_include_in_message_change)
        ttk.Checkbutton(
            row4,
            text="Incluir na mensagem",
            variable=self.include_in_message_var,
        ).pack(side=tk.RIGHT)

    def _on_date_change(self, *_):
        if self._updating_fields:
            return
        date = self.date_var.get().strip()
        detected = detect_weekday(date)
        if detected and detected != self.day_var.get():
            self._updating_fields = True
            self.day_var.set(detected)
            self._updating_fields = False
        self._on_field_change()

    def _on_day_change(self, *_):
        if self._updating_fields:
            return
        day = self.day_var.get().strip()
        if day:
            auto_date = next_occurrence_of_day(day)
            if auto_date and auto_date != self.date_var.get():
                self._updating_fields = True
                self.date_var.set(auto_date)
                self._updating_fields = False
        self._on_field_change()

    def _included_acolyte_ids(self):
        excluded = set(self.event.excluded_acolyte_ids)
        return [ac.id for ac in self.app.acolytes if ac.id not in excluded]

    def _refresh_participants_summary(self):
        for widget in self.participants_frame.winfo_children():
            widget.destroy()

        excluded_names = []
        for eid in self.event.excluded_acolyte_ids:
            ac = self.app.find_acolyte(eid)
            if ac:
                excluded_names.append(ac.name)

        if excluded_names:
            labels_frame = ttk.Frame(self.participants_frame)
            labels_frame.grid(row=0, column=0, sticky="w", pady=(2, 0))
            ttk.Label(
                labels_frame,
                text="excluído: ",
                font=("TkDefaultFont", 8),
                foreground="gray",
            ).pack(side=tk.LEFT)
            ttk.Label(
                labels_frame,
                text=", ".join(excluded_names),
                font=("TkDefaultFont", 8),
                foreground="gray",
            ).pack(side=tk.LEFT)

    def _on_field_change(self, *_):
        old_date = self.event.date
        old_time = self.event.time
        self.event.name = self.name_var.get().strip()
        self.event.date = normalize_date(self.date_var.get().strip())
        self.event.time = self.time_var.get().strip()

        datetime_changed = old_date != self.event.date or old_time != self.event.time
        if datetime_changed:
            self._apply_event_datetime_change(date_changed=(old_date != self.event.date))

        self._refresh_participants_summary()
        self.app.save()
        self.schedule_tab.maybe_refresh_cards_after_datetime_change()

    def _apply_event_datetime_change(self, date_changed: bool):
        """Auto include/exclude participants on datetime changes for activities."""
        warnings = []

        valid_date_for_reset = False
        if date_changed:
            try:
                datetime.strptime(self.event.date, "%d/%m/%Y")
                valid_date_for_reset = True
            except (TypeError, ValueError):
                valid_date_for_reset = False

        if date_changed and valid_date_for_reset and self.event.excluded_acolyte_ids:
            self.event.excluded_acolyte_ids = []
            warnings.append(
                "Data alterada: acólitos autoexcluídos foram incluídos novamente."
            )

        conflict_lines = []
        day = detect_weekday(self.event.date)
        for ac in self.app.acolytes:
            if ac.id in set(self.event.excluded_acolyte_ids):
                continue
            reason = _acolyte_unavailability_reason(ac, self.event.date, day, self.event.time)
            if reason:
                self.event.excluded_acolyte_ids.append(ac.id)
                conflict_lines.append(f"{ac.name}: {reason}")

        if conflict_lines:
            self.event.excluded_acolyte_ids = sorted(set(self.event.excluded_acolyte_ids))
            warnings.append(
                "Acólitos indisponíveis foram excluídos automaticamente da atividade. "
                "Edite os participantes se quiser incluí-los manualmente."
            )

        if warnings or conflict_lines:
            details = ""
            if conflict_lines:
                details = "\n\n" + "\n".join(conflict_lines)
            messagebox.showwarning(
                "Aviso de Indisponibilidade",
                "\n".join(warnings) + details,
                parent=self,
            )

    def _on_include_in_message_change(self, *_):
        self.event.include_in_message = bool(self.include_in_message_var.get())
        self.app.save()

    def _edit_included_acolytes(self):
        dlg = EditEventParticipantsDialog(
            self.app.root,
            self.app.acolytes,
            self.event.excluded_acolyte_ids,
        )
        if dlg.result is None:
            return
        self.event.excluded_acolyte_ids = list(dlg.result)
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
            )

            conflict_lines = []
            day = detect_weekday(date)
            for ac in self.app.acolytes:
                reason = _acolyte_unavailability_reason(ac, date, day, time)
                if reason:
                    ev.excluded_acolyte_ids.append(ac.id)
                    conflict_lines.append(f"{ac.name}: {reason}")
            ev.excluded_acolyte_ids = sorted(set(ev.excluded_acolyte_ids))

            self.app.general_events.append(ev)
            self.schedule_tab.refresh_cards()
            self.app.save()

            if conflict_lines:
                messagebox.showwarning(
                    "Aviso de Indisponibilidade",
                    "Alguns acólitos indisponíveis foram excluídos automaticamente da atividade. "
                    "Edite os participantes se quiser incluí-los manualmente.\n\n"
                    + "\n".join(conflict_lines),
                    parent=self.app.root,
                )

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
