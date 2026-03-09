"""Aba de criação de escalas e widget de slot de escala."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Optional

from ..models import (
    Acolyte,
    ScheduleSlot,
    ScheduleHistoryEntry,
    EventHistoryEntry,
    GeneratedScheduleSlotSnapshot,
    GeneratedSchedule,
    FinalizedEventBatch,
    FinalizedEventBatchEntry,
)
from ..utils import (
    WEEKDAYS_PT,
    detect_weekday,
    next_occurrence_of_day,
    normalize_date,
    names_list_to_text,
)
from .widgets import DateEntryFrame, TimeEntryFrame
from .dialogs import AddEventDialog, StandardSlotsDialog, FinalizeScheduleDialog, GeneralEventUnavailabilityDialog


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


class ScheduleSlotCard(ttk.LabelFrame):
    """Widget que representa um horário de escala."""

    def __init__(self, parent, slot: ScheduleSlot, app, **kwargs):
        title = (
            f"⛪ Atividade Geral #{slot.id[:6]}"
            if slot.is_general_event
            else f"Horário #{slot.id[:6]}"
        )
        super().__init__(parent, text=title, padding=6, **kwargs)
        self.slot = slot
        self.app = app
        self._acolyte_labels: dict = {}
        self._build()
        self._refresh_acolytes()

    def _build(self):
        self._date_trace_id = None
        self._day_trace_id = None

        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Data:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=self.slot.date)
        self._date_trace_id = self.date_var.trace_add("write", self._on_date_change)
        DateEntryFrame(row1, textvariable=self.date_var, width=6, date_format="DD/MM").pack(
            side=tk.LEFT, padx=2
        )

        ttk.Label(row1, text="Hora:").pack(side=tk.LEFT, padx=(6, 0))
        self.time_var = tk.StringVar(value=self.slot.time)
        self.time_var.trace_add("write", self._on_field_change)
        TimeEntryFrame(row1, textvariable=self.time_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Descrição:").pack(side=tk.LEFT, padx=(6, 0))
        self.desc_var = tk.StringVar(value=self.slot.description)
        self.desc_var.trace_add("write", self._on_field_change)
        ttk.Entry(row1, textvariable=self.desc_var, width=20).pack(side=tk.LEFT, padx=2)

        ttk.Button(row1, text="✕", width=3, command=self._remove_self).pack(
            side=tk.RIGHT, padx=2
        )

        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Dia:").pack(side=tk.LEFT)
        self.day_var = tk.StringVar(value=self.slot.day)
        self.day_combo = ttk.Combobox(
            row2, textvariable=self.day_var, values=WEEKDAYS_PT, width=16, state="readonly"
        )
        self.day_combo.pack(side=tk.LEFT, padx=2)
        self._day_trace_id = self.day_var.trace_add("write", self._on_day_change)

        self.acolyte_frame = ttk.Frame(self)
        self.acolyte_frame.pack(fill=tk.X, pady=2)

        row4 = ttk.Frame(self)
        row4.pack(fill=tk.X, pady=2)
        ttk.Button(
            row4,
            text="➕ Adicionar Acólito(s) Selecionado(s)",
            command=self._add_selected_acolytes,
        ).pack(side=tk.LEFT)

    def _on_date_change(self, *_):
        date = self.date_var.get().strip()
        detected = detect_weekday(date)
        if detected and detected != self.day_var.get():
            if self._day_trace_id:
                self.day_var.trace_remove("write", self._day_trace_id)
            self.day_var.set(detected)
            self._day_trace_id = self.day_var.trace_add("write", self._on_day_change)
        self._on_field_change()

    def _on_day_change(self, *_):
        day = self.day_var.get().strip()
        if day:
            auto_date = next_occurrence_of_day(day)
            if auto_date and auto_date != self.date_var.get():
                if self._date_trace_id:
                    self.date_var.trace_remove("write", self._date_trace_id)
                self.date_var.set(auto_date)
                self._date_trace_id = self.date_var.trace_add("write", self._on_date_change)
        self._on_field_change()

    def _on_field_change(self, *_):
        self.slot.date = normalize_date(self.date_var.get().strip())
        self.slot.time = self.time_var.get().strip()
        self.slot.description = self.desc_var.get().strip()
        self.slot.day = self.day_var.get()

    def _remove_self(self):
        if self.slot in self.app.schedule_slots:
            self.app.schedule_slots.remove(self.slot)
        self.destroy()
        self.app.save()

    def _add_selected_acolytes(self):
        acolytes = self.app.get_selected_acolytes_for_schedule()
        if not acolytes:
            messagebox.showinfo(
                "Aviso", "Selecione um ou mais acólitos na lista à direita.", parent=self
            )
            return
        added = []
        conflict_warnings = []
        for acolyte in acolytes:
            if acolyte.id not in self.slot.acolyte_ids:
                self.slot.acolyte_ids.append(acolyte.id)
                added.append(acolyte.name)
                # Check unavailability
                if self.slot.day and self.slot.time and hasattr(acolyte, 'unavailabilities'):
                    for unav in acolyte.unavailabilities:
                        if unav.day == self.slot.day and _time_in_interval(
                            self.slot.time, unav.start_time, unav.end_time
                        ):
                            conflict_warnings.append(
                                f"{acolyte.name}: indisponível às {self.slot.time} "
                                f"({unav.start_time}–{unav.end_time})"
                            )
                            break
        if added:
            self._refresh_acolytes()
            self.app.save()
            if conflict_warnings:
                messagebox.showwarning(
                    "Aviso de Indisponibilidade",
                    "Os seguintes acólitos foram adicionados, mas têm indisponibilidade neste horário:\n\n"
                    + "\n".join(conflict_warnings),
                    parent=self,
                )
        else:
            messagebox.showinfo(
                "Aviso", "Acólito(s) selecionado(s) já estão neste horário.", parent=self
            )

    def _remove_acolyte(self, acolyte_id: str):
        if acolyte_id in self.slot.acolyte_ids:
            self.slot.acolyte_ids.remove(acolyte_id)
        self._refresh_acolytes()
        self.app.save()

    def _refresh_acolytes(self):
        for widget in self.acolyte_frame.winfo_children():
            widget.destroy()
        self._acolyte_labels.clear()

        if self.slot.is_general_event:
            ttk.Label(
                self.acolyte_frame, text="TODOS",
                font=("TkDefaultFont", 10, "bold"), foreground="blue"
            ).pack(side=tk.LEFT)
            return

        if not self.slot.acolyte_ids:
            ttk.Label(self.acolyte_frame, text="(nenhum acólito)", foreground="gray").pack(
                side=tk.LEFT
            )
            return

        for aid in self.slot.acolyte_ids:
            acolyte = self.app.find_acolyte(aid)
            name = acolyte.name if acolyte else f"(id:{aid[:6]})"
            lbl_frame = ttk.Frame(self.acolyte_frame, relief="solid", padding=2)
            lbl_frame.pack(side=tk.LEFT, padx=2)
            ttk.Label(lbl_frame, text=name, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
            btn = ttk.Button(
                lbl_frame,
                text="✕",
                width=2,
                command=lambda aid=aid: self._remove_acolyte(aid),
            )
            btn.pack(side=tk.LEFT)
            self._acolyte_labels[aid] = lbl_frame

    def refresh(self):
        """Atualiza a exibição de acólitos."""
        self._refresh_acolytes()


class ScheduleTab(ttk.Frame):
    """Aba de criação de escalas."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._slot_cards: List[ScheduleSlotCard] = []
        self._build()

    def _build(self):
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Painel esquerdo ---
        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=640)

        header = ttk.Frame(left)
        header.pack(fill=tk.X, pady=4)
        ttk.Label(header, text="Criar Nova Escala", font=("TkDefaultFont", 12, "bold")).pack(
            side=tk.LEFT
        )

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row, text="➕ Adicionar Horário", command=self._add_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="⛪ Escala Geral", command=self._add_general_event_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="📋 Horários Padrão", command=self._manage_standard_slots).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="🗑️ Limpar Escala", command=self._clear_schedule).pack(
            side=tk.LEFT, padx=4
        )

        scroll_container = ttk.Frame(left)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, borderwidth=0, highlightthickness=0)
        v_scroll = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.slots_frame = ttk.Frame(canvas)
        self.slots_window = canvas.create_window((0, 0), window=self.slots_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.slots_window, width=canvas.winfo_width())

        self.slots_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.canvas = canvas

        ttk.Button(
            left,
            text="✅ Finalizar Escala",
            command=self._finalize_schedule,
            style="Accent.TButton",
        ).pack(fill=tk.X, pady=8, padx=4)

        # --- Painel direito ---
        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=210)

        ttk.Label(right, text="Acólitos", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        ctrl_frame = ttk.Frame(right)
        ctrl_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ctrl_frame, text="Ordem:").pack(side=tk.LEFT)
        self._sort_dir_var = tk.StringVar(value="asc")
        ttk.Radiobutton(
            ctrl_frame, text="↑ Crescente", variable=self._sort_dir_var,
            value="asc", command=self.refresh_acolyte_list,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            ctrl_frame, text="↓ Decrescente", variable=self._sort_dir_var,
            value="desc", command=self.refresh_acolyte_list,
        ).pack(side=tk.LEFT, padx=2)

        self._include_events_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right, text="Incluir atividades no total",
            variable=self._include_events_var,
            command=self.refresh_acolyte_list,
        ).pack(anchor="w", padx=4)

        ttk.Label(
            right, text="(Ctrl+clique para múltiplos)", foreground="gray",
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", padx=4)

        list_frame = ttk.Frame(right)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.acolyte_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("TkDefaultFont", 9),
            activestyle="dotbox",
        )
        self.acolyte_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.acolyte_listbox.yview)

    def refresh_acolyte_list(self):
        """Atualiza a lista de acólitos com opções de ordenação e filtro."""
        self.acolyte_listbox.delete(0, tk.END)

        include_events = getattr(self, '_include_events_var', None)
        sort_dir = getattr(self, '_sort_dir_var', None)

        def sort_key(a):
            base = a.times_scheduled
            if include_events and include_events.get():
                base += len(a.event_history)
            return base

        reverse = sort_dir is not None and sort_dir.get() == "desc"
        sorted_acolytes = sorted(self.app.acolytes, key=sort_key, reverse=reverse)
        self._sorted_acolytes_cache = sorted_acolytes

        for ac in sorted_acolytes:
            total = ac.times_scheduled
            if include_events and include_events.get():
                total += len(ac.event_history)
            suffix = " (suspenso)" if ac.is_suspended else ""
            self.acolyte_listbox.insert(tk.END, f"{ac.name}{suffix} ({total} escalas)")

        for i, ac in enumerate(sorted_acolytes):
            if ac.is_suspended:
                self.acolyte_listbox.itemconfig(i, foreground="red")

    def get_selected_acolyte(self) -> Optional[Acolyte]:
        acolytes = self.get_selected_acolytes()
        return acolytes[0] if acolytes else None

    def get_selected_acolytes(self) -> List[Acolyte]:
        sel = self.acolyte_listbox.curselection()
        if not sel:
            return []
        cache = getattr(self, '_sorted_acolytes_cache', None)
        if cache is None:
            self.refresh_acolyte_list()
            cache = getattr(self, '_sorted_acolytes_cache', [])
        result = []
        for idx in sel:
            if idx < len(cache):
                result.append(cache[idx])
        return result

    def _add_slot(self):
        slot = ScheduleSlot(id=str(uuid.uuid4()), date="", day="", time="")
        self.app.schedule_slots.append(slot)
        card = ScheduleSlotCard(self.slots_frame, slot, self.app)
        card.pack(fill=tk.X, padx=4, pady=4)
        self._slot_cards.append(card)
        self.app.save()

    def _add_general_event_slot(self):
        dlg = AddEventDialog(self.app.root)
        if dlg.result:
            name, date, time, include_as_activity, include_as_schedule = dlg.result

            all_acolyte_ids = [ac.id for ac in self.app.acolytes]
            day = detect_weekday(date)

            # Check unavailabilities
            excluded_ids = set()
            if time and day:
                conflicting = []
                for ac in self.app.acolytes:
                    if hasattr(ac, 'unavailabilities'):
                        for unav in ac.unavailabilities:
                            if unav.day == day and _time_in_interval(time, unav.start_time, unav.end_time):
                                conflicting.append(ac)
                                break
                if conflicting:
                    warn_dlg = GeneralEventUnavailabilityDialog(
                        self.app.root, name, time, day, conflicting
                    )
                    if warn_dlg.result is not None:
                        for ac in warn_dlg.result:
                            excluded_ids.add(ac.id)

            final_acolyte_ids = [aid for aid in all_acolyte_ids if aid not in excluded_ids]

            slot = ScheduleSlot(
                id=str(uuid.uuid4()),
                date=date,
                day=day,
                time=time,
                description=name,
                acolyte_ids=final_acolyte_ids,
                is_general_event=True,
                general_event_name=name,
                include_as_activity=include_as_activity,
                include_as_schedule=include_as_schedule,
            )
            self.app.schedule_slots.append(slot)
            card = ScheduleSlotCard(self.slots_frame, slot, self.app)
            card.pack(fill=tk.X, padx=4, pady=4)
            self._slot_cards.append(card)
            self.app.save()

    def _clear_schedule(self):
        if not self.app.schedule_slots:
            return
        if not messagebox.askyesno("Confirmar", "Deseja limpar todos os horários da escala?"):
            return
        self.app.schedule_slots.clear()
        self._slot_cards.clear()
        for widget in self.slots_frame.winfo_children():
            widget.destroy()
        self.app.save()

    def _manage_standard_slots(self):
        StandardSlotsDialog(self.app.root, self.app)
        self.refresh_acolyte_list()

    def load_slots_from_data(self):
        """Reconstrói os cards a partir dos dados carregados."""
        self._slot_cards.clear()
        for widget in self.slots_frame.winfo_children():
            widget.destroy()
        for slot in self.app.schedule_slots:
            card = ScheduleSlotCard(self.slots_frame, slot, self.app)
            card.pack(fill=tk.X, padx=4, pady=4)
            self._slot_cards.append(card)

    def _finalize_schedule(self):
        if not self.app.schedule_slots:
            messagebox.showinfo("Aviso", "Nenhum horário de escala criado.")
            return

        lines = ["*ESCALA DA SEMANA*\n"]
        general_event_slots = []
        for slot in self.app.schedule_slots:
            header = f"*{slot.day}, {slot.date} - {slot.time}:*"
            lines.append(header)
            if slot.description:
                lines.append(f"_{slot.description}_")
            if slot.is_general_event:
                lines.append("*TODOS*")
                general_event_slots.append(slot)
            else:
                names = []
                for aid in slot.acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac:
                        names.append(ac.name)
                lines.append(names_list_to_text(names))
            lines.append("")

        text = "\n".join(lines).strip()

        snapshot_slots = [
            GeneratedScheduleSlotSnapshot(
                slot_id=slot.id,
                date=slot.date,
                day=slot.day,
                time=slot.time,
                description=slot.description,
                acolyte_ids=list(slot.acolyte_ids),
            )
            for slot in self.app.schedule_slots
        ]
        gen_schedule = GeneratedSchedule(
            id=str(uuid.uuid4()),
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            schedule_text=text,
            slots=snapshot_slots,
        )
        self.app.generated_schedules.append(gen_schedule)

        for slot in self.app.schedule_slots:
            if not slot.is_general_event or slot.include_as_schedule:
                for aid in slot.acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac:
                        ac.times_scheduled += 1
                        entry = ScheduleHistoryEntry(
                            schedule_id=slot.id,
                            date=slot.date,
                            day=slot.day,
                            time=slot.time,
                            description=slot.description,
                        )
                        ac.schedule_history.append(entry)

        if general_event_slots:
            batch_id = str(uuid.uuid4())
            batch_entries = []

            for slot in general_event_slots:
                event_id = str(uuid.uuid4())
                event_name = slot.general_event_name or slot.description

                participating_acolyte_ids = [
                    ac.id for ac in self.app.acolytes if not ac.is_suspended
                ]

                batch_entry = FinalizedEventBatchEntry(
                    event_id=event_id,
                    name=event_name,
                    date=slot.date,
                    time=slot.time,
                    participating_acolyte_ids=participating_acolyte_ids,
                )
                batch_entries.append(batch_entry)

                for ac in self.app.acolytes:
                    if ac.id in participating_acolyte_ids:
                        hist_entry = EventHistoryEntry(
                            event_id=event_id,
                            name=event_name,
                            date=slot.date,
                            time=slot.time,
                        )
                        ac.event_history.append(hist_entry)

            batch = FinalizedEventBatch(
                id=batch_id,
                finalized_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
                entries=batch_entries,
            )
            self.app.finalized_event_batches.append(batch)

        self.app.schedule_slots.clear()
        self._slot_cards.clear()
        for widget in self.slots_frame.winfo_children():
            widget.destroy()

        self.app.save()
        self.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()
        self.app.events_tab.refresh_list()

        if hasattr(self.app, 'history_tab'):
            self.app.history_tab.refresh()

        FinalizeScheduleDialog(self.app.root, text)
