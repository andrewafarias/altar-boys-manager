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
from .dialogs import (
    AddEscalaGeralDialog,
    StandardSlotsDialog,
    FinalizeScheduleDialog,
    GeneralEventUnavailabilityDialog,
    EditGeneralEventExcludedDialog,
)
from .events_tab import EventsTab


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


def _sort_key_date_time(date_str: str, time_str: str):
    """Sort by date/time, keeping items without time at the end of their day."""
    date_text = (date_str or "").strip()
    time_text = (time_str or "").strip()

    date_rank = 1
    date_value = (9999, 12, 31)
    if date_text:
        parts = date_text.split("/")
        try:
            if len(parts) == 2:
                day, month = int(parts[0]), int(parts[1])
                year = datetime.now().year
                date_rank = 0
                date_value = (year, month, day)
            elif len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                date_rank = 0
                date_value = (year, month, day)
        except (ValueError, TypeError):
            pass

    # Items with empty/invalid time go after valid times for the same date.
    time_rank = 1
    time_value = 24 * 60
    if time_text:
        try:
            parsed_time = datetime.strptime(time_text, "%H:%M")
            time_rank = 0
            time_value = parsed_time.hour * 60 + parsed_time.minute
        except ValueError:
            pass

    return date_rank, date_value, time_rank, time_value


class ScheduleSlotCard(ttk.LabelFrame):
    """Widget que representa um horário de escala."""

    def __init__(self, parent, slot: ScheduleSlot, app, schedule_tab, **kwargs):
        title = (
            f"Escala Geral #{slot.id[:6]}"
            if slot.is_general_event
            else f"Horário #{slot.id[:6]}"
        )
        super().__init__(parent, text=title, padding=6, **kwargs)
        self.slot = slot
        self.app = app
        self.schedule_tab = schedule_tab
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
        
        if not self.slot.is_general_event:
            ttk.Button(
                row4,
                text="➕ Adicionar Acólito(s) Selecionado(s)",
                command=self._add_selected_acolytes,
            ).pack(side=tk.LEFT)

        if self.slot.is_general_event:
            ttk.Button(
                row4,
                text="✏️ Editar Excluídos",
                command=self._edit_general_event_excluded,
            ).pack(side=tk.LEFT, padx=(6, 0))

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
        # Check unavailability when editing date/time
        self._check_unavailability_on_edit()
        self.app.save()
        self.schedule_tab.maybe_refresh_cards_after_datetime_change()

    def _check_unavailability_on_edit(self):
        """Check if any currently assigned acolytes are unavailable with the new date/time."""
        if not self.slot.day or not self.slot.time or not self.slot.acolyte_ids:
            return
        
        conflict_warnings = []
        for aid in self.slot.acolyte_ids:
            acolyte = self.app.find_acolyte(aid)
            if acolyte and hasattr(acolyte, 'unavailabilities'):
                for unav in acolyte.unavailabilities:
                    if unav.day == self.slot.day and _time_in_interval(
                        self.slot.time, unav.start_time, unav.end_time
                    ):
                        conflict_warnings.append(
                            f"{acolyte.name}: indisponível às {self.slot.time} "
                            f"({unav.start_time}–{unav.end_time})"
                        )
                        break
        
        if conflict_warnings:
            messagebox.showwarning(
                "Aviso de Indisponibilidade",
                "Os seguintes acólitos têm indisponibilidade no novo horário:\n\n"
                + "\n".join(conflict_warnings),
                parent=self,
            )

    def _remove_self(self):
        if self.slot in self.app.schedule_slots:
            self.app.schedule_slots.remove(self.slot)
        self.schedule_tab.refresh_cards()
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

    def _edit_general_event_excluded(self):
        if not self.slot.is_general_event:
            return

        include_suspended = getattr(self.app, "include_suspended_in_general_event", True)
        suspended_locked_ids = []
        if not include_suspended:
            suspended_locked_ids = [ac.id for ac in self.app.acolytes if ac.is_suspended]

        # Build current excluded ids from both sources.
        current_excluded = set(self.slot.excluded_acolyte_ids)
        current_excluded.update(self.slot.suspended_excluded_acolyte_ids)

        dlg = EditGeneralEventExcludedDialog(
            self.app.root,
            self.app.acolytes,
            list(current_excluded),
            suspended_locked_ids=suspended_locked_ids,
        )
        if dlg.result is None:
            return

        selected_excluded = set(dlg.result)
        suspended_set = set(suspended_locked_ids)

        self.slot.suspended_excluded_acolyte_ids = sorted(suspended_set)
        self.slot.excluded_acolyte_ids = sorted(selected_excluded - suspended_set)

        # Recompute included acolytes for this general slot.
        excluded_union = set(self.slot.excluded_acolyte_ids) | set(self.slot.suspended_excluded_acolyte_ids)
        self.slot.acolyte_ids = [ac.id for ac in self.app.acolytes if ac.id not in excluded_union]

        self._refresh_acolytes()
        self.app.save()

    def _is_acolyte_unavailable(self, acolyte_id: str) -> bool:
        """Check if an acolyte is unavailable at this slot's day/time."""
        if not self.slot.day or not self.slot.time:
            return False
        
        acolyte = self.app.find_acolyte(acolyte_id)
        if not acolyte or not hasattr(acolyte, 'unavailabilities'):
            return False
        
        for unav in acolyte.unavailabilities:
            if unav.day == self.slot.day and _time_in_interval(
                self.slot.time, unav.start_time, unav.end_time
            ):
                return True
        return False

    def _format_excluded_indicator(self, entries: List[str], max_chars: int = 90) -> str:
        """Format excluded names and truncate long text to avoid UI overflow."""
        if not entries:
            return ""

        full_text = ", ".join(entries)
        if len(full_text) <= max_chars:
            return full_text

        shown = []
        current_len = 0
        for name in entries:
            add_len = len(name) + (2 if shown else 0)
            # Keep room for trailing "... (+N)"
            if current_len + add_len > max_chars - 12:
                break
            shown.append(name)
            current_len += add_len

        remaining = len(entries) - len(shown)
        if not shown:
            return f"{entries[0]}... (+{len(entries) - 1})"
        if remaining > 0:
            return f"{', '.join(shown)}... (+{remaining})"
        return ", ".join(shown)

    def _refresh_acolytes(self):
        for widget in self.acolyte_frame.winfo_children():
            widget.destroy()
        self._acolyte_labels.clear()

        if self.slot.is_general_event:
            row_frame = ttk.Frame(self.acolyte_frame)
            row_frame.grid(row=0, column=0, sticky="w")
            
            ttk.Label(
                row_frame, text="TODOS",
                font=("TkDefaultFont", 10, "bold"), foreground="blue"
            ).pack(side=tk.LEFT)
            
            # Show excluded acolytes indicator (including suspended exclusions)
            excluded_names = []
            for eid in self.slot.excluded_acolyte_ids:
                ac = self.app.find_acolyte(eid)
                if ac:
                    excluded_names.append(ac.name)

            suspended_excluded_names = []
            for eid in self.slot.suspended_excluded_acolyte_ids:
                ac = self.app.find_acolyte(eid)
                if ac:
                    suspended_excluded_names.append(ac.name)

            if excluded_names or suspended_excluded_names:
                # Create a frame to hold multiple labels with different colors
                labels_frame = ttk.Frame(self.acolyte_frame)
                labels_frame.grid(row=1, column=0, sticky="w", pady=(2, 0))
                
                # Label for "excluído: " prefix
                ttk.Label(
                    labels_frame,
                    text="excluído: ",
                    font=("TkDefaultFont", 8),
                    foreground="gray",
                ).pack(side=tk.LEFT)
                
                # Label for regular excluded names
                if excluded_names:
                    formatted_excluded = ", ".join(excluded_names)
                    ttk.Label(
                        labels_frame,
                        text=formatted_excluded,
                        font=("TkDefaultFont", 8),
                        foreground="gray",
                    ).pack(side=tk.LEFT)
                
                # Separator comma if both types exist
                if excluded_names and suspended_excluded_names:
                    ttk.Label(
                        labels_frame,
                        text=", ",
                        font=("TkDefaultFont", 8),
                        foreground="gray",
                    ).pack(side=tk.LEFT)
                
                # Label for suspended excluded names (light red)
                if suspended_excluded_names:
                    formatted_suspended = ", ".join(suspended_excluded_names)
                    tk.Label(
                        labels_frame,
                        text=formatted_suspended,
                        font=("TkDefaultFont", 8),
                        foreground="#ff6b6b",
                    ).pack(side=tk.LEFT)
            
            return

        if not self.slot.acolyte_ids:
            ttk.Label(self.acolyte_frame, text="(nenhum acólito)", foreground="gray").grid(
                row=0, column=0, sticky="w"
            )
            return

        max_cols = 5
        for i, aid in enumerate(self.slot.acolyte_ids):
            acolyte = self.app.find_acolyte(aid)
            name = acolyte.name if acolyte else f"(id:{aid[:6]})"
            
            # Check if acolyte is unavailable at this time
            is_unavailable = self._is_acolyte_unavailable(aid)
            
            # Use tk.Frame with light red background if unavailable, otherwise use ttk.Frame
            if is_unavailable:
                lbl_frame = tk.Frame(
                    self.acolyte_frame, relief="solid", bd=1, bg="#FFCCCC", padx=2, pady=2
                )
                name_label = tk.Label(lbl_frame, text=name, font=("TkDefaultFont", 8), bg="#FFCCCC")
            else:
                lbl_frame = ttk.Frame(self.acolyte_frame, relief="solid", padding=2)
                name_label = ttk.Label(lbl_frame, text=name, font=("TkDefaultFont", 8))
            
            lbl_frame.grid(row=i // max_cols, column=i % max_cols, padx=2, pady=1, sticky="w")
            
            name_label.pack(side=tk.LEFT)
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
        self._rendered_card_order: List[str] = []
        self._build()

    def _build(self):
        paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED,
            sashwidth=5,
        )
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
        ttk.Button(btn_row, text="✨ Adicionar Atividade", command=self._add_event).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="⛪ Escala Geral", command=self._add_general_event_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="📋 Escala Padrão", command=self._manage_standard_slots).pack(
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

        self.cards_frame = ttk.Frame(self.slots_frame)
        self.cards_frame.pack(fill=tk.X, expand=True)

        self.events_tab = EventsTab(self.app, self)

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.slots_window, width=canvas.winfo_width())

        self.slots_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        def _on_mousewheel(event):
            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):
                step = -1 if event.delta > 0 else 1
                canvas.yview_scroll(step, "units")

        def _bind_scroll(_evt=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
            canvas.bind_all("<Button-4>", _on_mousewheel, add="+")
            canvas.bind_all("<Button-5>", _on_mousewheel, add="+")

        def _unbind_scroll(_evt=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_scroll)
        canvas.bind("<Leave>", _unbind_scroll)

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

    def refresh_cards(self):
        sorted_cards = self._sorted_card_items()
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        rendered_order: List[str] = []
        for item_type, item in sorted_cards:
            if item_type == "slot":
                card = ScheduleSlotCard(self.cards_frame, item, self.app, self)
            else:
                card = self.events_tab.create_card(self.cards_frame, item)
            card.pack(fill=tk.X, padx=4, pady=4)
            rendered_order.append(self._card_token(item_type, item.id))

        self._rendered_card_order = rendered_order

    def _card_token(self, item_type: str, item_id: str) -> str:
        return f"{item_type}:{item_id}"

    def _sorted_card_items(self):
        merged_items = []
        for idx, slot in enumerate(self.app.schedule_slots):
            merged_items.append(("slot", slot, idx))

        event_offset = len(merged_items)
        for idx, event in enumerate(self.app.general_events):
            merged_items.append(("event", event, event_offset + idx))

        merged_items.sort(
            key=lambda entry: (
                *_sort_key_date_time(entry[1].date, entry[1].time),
                entry[2],
            )
        )
        return [(item_type, item) for item_type, item, _ in merged_items]

    def maybe_refresh_cards_after_datetime_change(self):
        sorted_cards = self._sorted_card_items()
        expected_order = [
            self._card_token(item_type, item.id)
            for item_type, item in sorted_cards
        ]

        if expected_order != self._rendered_card_order:
            self.refresh_cards()

    def _add_slot(self):
        slot = ScheduleSlot(
            id=str(uuid.uuid4()),
            date="",
            day="",
            time="",
        )
        self.app.schedule_slots.append(slot)
        self.refresh_cards()
        self.app.save()

    def _add_event(self):
        self.events_tab.add_event()

    def _add_general_event_slot(self):
        dlg = AddEscalaGeralDialog(self.app.root)
        if dlg.result:
            name, date, time, include_as_activity, include_as_schedule = dlg.result

            include_suspended = getattr(self.app, "include_suspended_in_general_event", True)
            suspended_excluded_ids = [
                ac.id for ac in self.app.acolytes
                if ac.is_suspended and not include_suspended
            ]
            eligible_acolytes = [
                ac for ac in self.app.acolytes
                if include_suspended or not ac.is_suspended
            ]
            all_acolyte_ids = [ac.id for ac in eligible_acolytes]
            day = detect_weekday(date)

            # Check unavailabilities
            excluded_ids = set()
            if time and day:
                conflicting = []
                for ac in eligible_acolytes:
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
                excluded_acolyte_ids=list(excluded_ids),
                suspended_excluded_acolyte_ids=suspended_excluded_ids,
            )
            self.app.schedule_slots.append(slot)
            self.refresh_cards()
            self.app.save()

    def _clear_schedule(self):
        if not self.app.schedule_slots and not self.app.general_events:
            return
        if not messagebox.askyesno("Confirmar", "Deseja limpar todos os cards da escala?"):
            return
        self.app.schedule_slots.clear()
        self.app.general_events.clear()
        self.refresh_cards()
        self.app.save()

    def _manage_standard_slots(self):
        StandardSlotsDialog(self.app.root, self.app)
        self.refresh_acolyte_list()

    def load_slots_from_data(self, adapt_dates: bool = False):
        """Reconstrói os cards a partir dos dados carregados.

        Args:
            adapt_dates: When True, updates each slot's date to the next
                occurrence of its weekday before rebuilding cards. Used at
                app startup so persisted slots show upcoming dates.
        """
        if adapt_dates:
            for slot in self.app.schedule_slots:
                if slot.day:
                    slot.date = next_occurrence_of_day(slot.day)
        self.refresh_cards()

    def _finalize_schedule(self):
        if not self.app.schedule_slots and not self.app.general_events:
            messagebox.showinfo("Aviso", "Nenhum horário ou atividade criado.")
            return

        # Auto-populate general event slots that have empty acolyte_ids (reused after previous finalization)
        for slot in self.app.schedule_slots:
            if slot.is_general_event and not slot.acolyte_ids:
                slot.acolyte_ids = [ac.id for ac in self.app.acolytes]

        lines = ["*ESCALA DA SEMANA*\n"]
        general_event_slots = []
        message_items = []

        for slot in self.app.schedule_slots:
            if slot.is_general_event:
                general_event_slots.append(slot)

            if slot.is_general_event:
                detail_line = "*TODOS*"
            else:
                names = []
                for aid in slot.acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac:
                        names.append(ac.name)
                detail_line = names_list_to_text(names)

            message_items.append(
                {
                    "date": slot.date,
                    "time": slot.time,
                    "day": slot.day,
                    "description": slot.description,
                    "detail": detail_line,
                }
            )

        for ev in self.app.general_events:
            if not ev.include_in_message:
                continue
            message_items.append(
                {
                    "date": ev.date,
                    "time": ev.time,
                    "day": detect_weekday(ev.date) or "",
                    "description": ev.name,
                    "detail": None,
                }
            )

        for item in message_items:
            header = f"*{item['day']}, {item['date']}"
            if item["time"]:
                header += f" - {item['time']}"
            header += ":*"
            lines.append(header)
            if item["description"]:
                lines.append(f"_{item['description']}_")
            if item["detail"] is not None:
                lines.append(item["detail"])
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
                is_general_event=slot.is_general_event,
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
                if not slot.include_as_activity:
                    continue

                event_id = str(uuid.uuid4())
                event_name = slot.general_event_name or slot.description

                participating_acolyte_ids = []
                for aid in slot.acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac and not ac.is_suspended:
                        participating_acolyte_ids.append(aid)

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

            if batch_entries:
                batch = FinalizedEventBatch(
                    id=batch_id,
                    finalized_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
                    entries=batch_entries,
                )
                self.app.finalized_event_batches.append(batch)
                gen_schedule.batch_id = batch_id

        self.app.events_tab.finalize_pending_events()

        # Reset slots for reuse: new IDs, clear acolytes, update dates
        for slot in self.app.schedule_slots:
            slot.id = str(uuid.uuid4())
            slot.acolyte_ids = []
            if slot.day:
                slot.date = next_occurrence_of_day(slot.day)

        self.load_slots_from_data()

        self.app.save()
        self.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()
        self.app.events_tab.refresh_list()

        if hasattr(self.app, 'history_tab'):
            self.app.history_tab.refresh()

        FinalizeScheduleDialog(self.app.root, text)
