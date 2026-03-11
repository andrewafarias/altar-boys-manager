"""Aba de calendário com visualização mensal e linha do tempo."""

import calendar as cal_module
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import List, Dict, Optional

from ..models import (
    Absence,
    ScheduleSlot,
    GeneralEvent,
    Acolyte,
    GeneratedScheduleSlotSnapshot,
    ScheduleHistoryEntry,
    EventHistoryEntry,
)
from ..utils import detect_weekday


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

_DAY_HEADERS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def _parse_date(date_str: str) -> Optional[date]:
    """Parse DD/MM/YYYY or DD/MM into a date object."""
    if not date_str:
        return None
    try:
        parts = date_str.strip().split("/")
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
        if len(parts) == 2:
            return date(datetime.now().year, int(parts[1]), int(parts[0]))
    except (ValueError, IndexError):
        pass
    return None


def _format_date(d: date) -> str:
    """Format a date as DD/MM/YYYY."""
    return d.strftime("%d/%m/%Y")


def _birthdate_matches_day(birthdate_str: str, day: int, month: int) -> bool:
    """Check if an acolyte's birthdate (DD/MM/YYYY) matches a given day/month."""
    if not birthdate_str:
        return False
    try:
        parts = birthdate_str.strip().split("/")
        return int(parts[0]) == day and int(parts[1]) == month
    except (ValueError, IndexError):
        return False


# ---------------------------------------------------------------------------
# Data structures for calendar entries
# ---------------------------------------------------------------------------

class DayInfo:
    """Aggregated information for a single calendar day."""

    __slots__ = ("date_obj", "birthdays", "schedule_slots", "general_events",
                 "history_slots", "history_events")

    def __init__(self, date_obj: date):
        self.date_obj = date_obj
        self.birthdays: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []
        self.history_slots: List[dict] = []  # from generated schedules
        self.history_events: List[dict] = []  # from finalized event batches

    @property
    def has_content(self) -> bool:
        return bool(self.birthdays or self.schedule_slots or self.general_events
                     or self.history_slots or self.history_events)


# ---------------------------------------------------------------------------
# Day Detail Dialog (shown when user clicks a day)
# ---------------------------------------------------------------------------

class DayDetailDialog(tk.Toplevel):
    """Pop-up showing details and absence tools for a specific day."""

    def __init__(self, parent, app, day_info: DayInfo):
        super().__init__(parent)
        self.app = app
        self.day_info = day_info
        self._row_action_frames: Dict[tuple, List[ttk.Frame]] = {}
        self._entry_refs: Dict[tuple, object] = {}
        self.title(f"📅 {_format_date(day_info.date_obj)}")
        self.resizable(True, True)
        self.minsize(900, 700)
        self.grab_set()
        self._build()
        self._fit_to_content()

    def _fit_to_content(self):
        """Resize dialog proportionally to its content, capped at screen size."""
        self.update_idletasks()
        req_w = max(self.winfo_reqwidth(), 900)
        req_h = max(self.winfo_reqheight(), 700)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(req_w + 40, int(sw * 0.9))
        h = min(req_h + 40, int(sh * 0.85))
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # -- build ---------------------------------------------------------------

    def _build(self):
        paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5,
        )
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Left panel: scrollable content (units/absences) ----------------
        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=500)

        canvas = tk.Canvas(left, highlightthickness=0)
        vscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = ttk.Frame(canvas)
        self._canvas_win_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas = canvas

        def _on_configure(_evt):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._inner.bind("<Configure>", _on_configure)

        def _on_canvas_resize(event):
            canvas.itemconfigure(self._canvas_win_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        # Cross-platform mousewheel scrolling
        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                canvas.yview_scroll(3, "units")
            elif event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll(_evt=None):
            canvas.bind_all("<Button-4>", _on_mousewheel, add="+")
            canvas.bind_all("<Button-5>", _on_mousewheel, add="+")
            canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        def _unbind_scroll(_evt=None):
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            canvas.unbind_all("<MouseWheel>")

        self.bind("<FocusIn>", _bind_scroll)
        self.bind("<Destroy>", _unbind_scroll)
        _bind_scroll()

        # Build left content
        self._build_left_content()

        # --- Right panel: falta rápida --------------------------------------
        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=220)
        self._right_panel = right
        self._build_right_panel()

    def _build_left_content(self):
        """Build the left panel content (units with individual absence buttons)."""
        self._row_action_frames = {}
        self._entry_refs = {}

        # -- Birthdays -------------------------------------------------------
        if self.day_info.birthdays:
            lf = ttk.LabelFrame(self._inner, text="🎂 Aniversariantes", padding=6)
            lf.pack(fill=tk.X, pady=(0, 6))
            for ac in self.day_info.birthdays:
                ttk.Label(lf, text=f"• {ac.name}").pack(anchor="w")

        # -- Per-unit sections -----------------------------------------------
        for slot in self.day_info.schedule_slots:
            self._build_unit_section(slot, is_schedule=True, allow_absence=False)

        for evt in self.day_info.general_events:
            self._build_unit_section(evt, is_schedule=False, allow_absence=False)

        # History entries
        for h_slot in self.day_info.history_slots:
            snap = h_slot["snapshot"]
            self._build_history_unit_section(snap, is_schedule=True)

        for h_evt in self.day_info.history_events:
            entry = h_evt["entry"]
            self._build_history_unit_section(entry, is_schedule=False)

        # -- Close button ----------------------------------------------------
        ttk.Button(self._inner, text="Fechar", command=self.destroy).pack(pady=8)

    def _build_right_panel(self):
        """Build the right panel with falta rápida list and buttons."""
        right = self._right_panel

        ttk.Label(right, text="⚡ Falta Rápida",
                  font=("TkDefaultFont", 11, "bold")).pack(pady=4)
        ttk.Label(right, text="Marcar ausência em\nunidades finalizadas do dia",
                  foreground="gray", font=("TkDefaultFont", 8),
                  justify="center").pack(anchor="center")

        all_acolytes_in_day = self._get_finalized_acolytes_in_day()

        ttk.Label(right, text="(Ctrl+clique para múltiplos)",
                  foreground="gray", font=("TkDefaultFont", 8)).pack(anchor="w", padx=4)

        list_frame = ttk.Frame(right)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._quick_ac_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("TkDefaultFont", 9),
            activestyle="dotbox",
        )
        self._quick_ac_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._quick_ac_listbox.yview)

        self._quick_ac_sorted = sorted(all_acolytes_in_day, key=lambda a: a.name)
        for ac in self._quick_ac_sorted:
            self._quick_ac_listbox.insert(tk.END, ac.name)

        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(
            btn_frame, text="Tudo como falta real",
            command=lambda: self._quick_absence_all(symbolic=False),
        ).pack(fill=tk.X, pady=1)
        ttk.Button(
            btn_frame, text="1 real + resto simbólica",
            command=lambda: self._quick_absence_all(symbolic=True),
        ).pack(fill=tk.X, pady=1)

        if not self._quick_ac_sorted:
            self._quick_ac_listbox.configure(state=tk.DISABLED)
            for child in btn_frame.winfo_children():
                child.configure(state=tk.DISABLED)
            ttk.Label(
                right,
                text="Sem unidades finalizadas neste dia.",
                foreground="gray",
                font=("TkDefaultFont", 8),
            ).pack(anchor="w", padx=4, pady=(2, 0))

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Button(
            right, text="Limpar faltas",
            command=self._clear_all_absences,
        ).pack(fill=tk.X, padx=4, pady=1)

    # -- helpers -------------------------------------------------------------

    def _get_finalized_acolytes_in_day(self) -> List[Acolyte]:
        """Return deduplicated list of acolytes participating in finalized/history units."""
        ids = set()
        for h_slot in self.day_info.history_slots:
            ids.update(h_slot["snapshot"].acolyte_ids)
        for h_evt in self.day_info.history_events:
            ids.update(h_evt["entry"].participating_acolyte_ids)
        return [ac for ac in self.app.acolytes if ac.id in ids]

    def _get_participants(self, unit, is_schedule: bool) -> List[Acolyte]:
        if is_schedule:
            slot: ScheduleSlot = unit
            if slot.is_general_event or not slot.acolyte_ids:
                return [ac for ac in self.app.acolytes
                        if ac.id not in slot.excluded_acolyte_ids]
            return [ac for ac in self.app.acolytes if ac.id in slot.acolyte_ids]
        else:
            evt: GeneralEvent = unit
            return [ac for ac in self.app.acolytes
                    if ac.id not in evt.excluded_acolyte_ids]

    def _unit_label(self, unit, is_schedule: bool) -> str:
        if is_schedule:
            slot: ScheduleSlot = unit
            parts = []
            if slot.is_general_event:
                parts.append(f"⛪ {slot.general_event_name or 'Escala Geral'}")
            else:
                parts.append("📋 Escala")
            if slot.time:
                parts.append(f"({slot.time})")
            if slot.description:
                parts.append(f"— {slot.description}")
            return " ".join(parts)
        else:
            evt: GeneralEvent = unit
            parts = [f"✨ {evt.name}"]
            if evt.time:
                parts.append(f"({evt.time})")
            return " ".join(parts)

    def _register_entry_ref(self, entry_type: str, entry_id: str, unit):
        self._entry_refs[(entry_type, entry_id)] = unit

    def _build_linked_absence_description(self, entry_type: str, unit, date_str: str) -> str:
        label = "atividade" if entry_type == "event" else "escala"
        if entry_type == "event":
            detail = getattr(unit, "name", "") or "Sem descrição"
        else:
            detail = (
                getattr(unit, "description", "")
                or getattr(unit, "general_event_name", "")
                or "Sem descrição"
            )
        time_str = getattr(unit, "time", "") or "-"
        return f"Faltou {label}: {detail} {date_str} {time_str}"

    def _set_linked_missed_flag(self, acolyte: Acolyte, entry_type: str, entry_id: str, missed: bool):
        unit = self._entry_refs.get((entry_type, entry_id))
        date_str = getattr(unit, "date", "") or _format_date(self.day_info.date_obj)

        if entry_type == "schedule":
            found = False
            for entry in acolyte.schedule_history:
                if entry.schedule_id == entry_id:
                    entry.missed = missed
                    found = True
            if not found and missed:
                day_str = getattr(unit, "day", "") or detect_weekday(date_str)
                time_str = getattr(unit, "time", "") or ""
                desc = (
                    getattr(unit, "description", "")
                    or getattr(unit, "general_event_name", "")
                    or ""
                )
                acolyte.schedule_history.append(
                    ScheduleHistoryEntry(
                        schedule_id=entry_id,
                        date=date_str,
                        day=day_str,
                        time=time_str,
                        description=desc,
                        missed=True,
                    )
                )
        elif entry_type == "event":
            found = False
            for entry in acolyte.event_history:
                if entry.event_id == entry_id:
                    entry.missed = missed
                    found = True
            if not found and missed:
                name = getattr(unit, "name", "") or getattr(unit, "general_event_name", "") or "Atividade"
                time_str = getattr(unit, "time", "") or ""
                acolyte.event_history.append(
                    EventHistoryEntry(
                        event_id=entry_id,
                        name=name,
                        date=date_str,
                        time=time_str,
                        missed=True,
                    )
                )

    def _refresh_acolyte_table_if_needed(self, updated_acolyte_ids: set):
        ac_tab = getattr(self.app, "acolytes_tab", None)
        if ac_tab is None:
            return
        ac_tab.refresh_list()
        current = getattr(ac_tab, "_current_acolyte", None)
        if current and current.id in updated_acolyte_ids:
            ac_tab._show_acolyte_detail()

    def _upsert_linked_absence(
        self,
        acolyte: Acolyte,
        entry_type: str,
        unit_id: str,
        date_str: str,
        *,
        symbolic: bool,
    ):
        unit = self._entry_refs.get((entry_type, unit_id))
        description = (
            self._build_linked_absence_description(entry_type, unit, date_str)
            if unit is not None
            else "Registrada via calendário"
        )

        existing = self._find_absence(acolyte, unit_id, date_str)
        if existing:
            existing.description = description
            existing.linked_entry_type = entry_type
            existing.linked_entry_id = unit_id
            existing.is_symbolic = symbolic
        else:
            acolyte.absences.append(
                Absence(
                    date=date_str,
                    description=description,
                    linked_entry_type=entry_type,
                    linked_entry_id=unit_id,
                    is_symbolic=symbolic,
                )
            )

        self._set_linked_missed_flag(acolyte, entry_type, unit_id, True)

    def _find_absence(self, acolyte: Acolyte, unit_id: str, date_str: str) -> Optional[Absence]:
        return next(
            (a for a in acolyte.absences if a.date == date_str and a.linked_entry_id == unit_id),
            None,
        )

    def _register_row_action_frame(
        self, acolyte_id: str, unit_id: str, entry_type: str, frame: ttk.Frame
    ):
        key = (acolyte_id, unit_id, entry_type)
        self._row_action_frames.setdefault(key, []).append(frame)

    def _render_row_actions(
        self,
        action_frame: ttk.Frame,
        acolyte: Acolyte,
        unit_id: str,
        entry_type: str,
        date_str: str,
        small_font,
    ):
        for widget in action_frame.winfo_children():
            widget.destroy()

        absence_obj = self._find_absence(acolyte, unit_id, date_str)
        if absence_obj:
            tk.Button(
                action_frame,
                text="Remover",
                font=small_font,
                padx=2,
                pady=0,
                command=lambda a=acolyte, uid=unit_id, ds=date_str: self._remove_absence(a, uid, ds),
            ).pack(side=tk.LEFT, padx=1)
            kind = "simb." if absence_obj.is_symbolic else "real"
            ttk.Label(
                action_frame,
                text=f"✗ Falta ({kind})",
                foreground="red",
                font=small_font,
            ).pack(side=tk.LEFT, padx=2)
            return

        tk.Button(
            action_frame,
            text="Real",
            font=small_font,
            padx=2,
            pady=0,
            command=lambda a=acolyte, uid=unit_id, et=entry_type, ds=date_str: (
                self._add_absence(a, uid, et, ds, symbolic=False)
            ),
        ).pack(side=tk.LEFT, padx=1)
        tk.Button(
            action_frame,
            text="Simb.",
            font=small_font,
            padx=2,
            pady=0,
            command=lambda a=acolyte, uid=unit_id, et=entry_type, ds=date_str: (
                self._add_absence(a, uid, et, ds, symbolic=True)
            ),
        ).pack(side=tk.LEFT, padx=1)

    def _refresh_row_actions(self, acolyte: Acolyte, unit_id: str, entry_type: str, date_str: str):
        key = (acolyte.id, unit_id, entry_type)
        for frame in self._row_action_frames.get(key, []):
            self._render_row_actions(frame, acolyte, unit_id, entry_type, date_str, ("TkDefaultFont", 8))

    def _refresh_all_row_actions(self):
        acolytes_by_id = {ac.id: ac for ac in self.app.acolytes}
        date_str = _format_date(self.day_info.date_obj)
        for (ac_id, unit_id, entry_type), frames in self._row_action_frames.items():
            acolyte = acolytes_by_id.get(ac_id)
            if acolyte is None:
                continue
            for frame in frames:
                self._render_row_actions(
                    frame,
                    acolyte,
                    unit_id,
                    entry_type,
                    date_str,
                    ("TkDefaultFont", 8),
                )

    # -- build a single unit section -----------------------------------------

    def _build_unit_section(self, unit, *, is_schedule: bool, allow_absence: bool):
        label = self._unit_label(unit, is_schedule)
        participants = self._get_participants(unit, is_schedule)
        unit_id = unit.id
        entry_type = "schedule" if is_schedule else "event"
        if allow_absence:
            self._register_entry_ref(entry_type, unit_id, unit)

        lf = ttk.LabelFrame(self._inner, text=label, padding=6)
        lf.pack(fill=tk.X, pady=(0, 6))

        if not allow_absence:
            ttk.Label(
                lf,
                text="Planejamento (faltas desabilitadas)",
                foreground="gray",
                font=("TkDefaultFont", 8),
            ).pack(anchor="w", pady=(0, 2))

        if not participants:
            ttk.Label(lf, text="Nenhum acólito participante.").pack(anchor="w")
            return

        date_str = _format_date(self.day_info.date_obj)
        _sm = ("TkDefaultFont", 8)

        # For each participant, a row with name + absence buttons
        for ac in sorted(participants, key=lambda a: a.name):
            row = ttk.Frame(lf)
            row.pack(fill=tk.X, pady=0)

            display_name = ac.name if len(ac.name) <= 20 else ac.name[:18] + "…"
            ttk.Label(row, text=display_name, width=20, anchor="w", font=_sm).pack(side=tk.LEFT)

            if not allow_absence:
                ttk.Label(
                    row,
                    text="Sem marcação de falta",
                    foreground="gray",
                    font=_sm,
                ).pack(side=tk.LEFT, padx=2)
                continue

            actions = ttk.Frame(row)
            actions.pack(side=tk.LEFT)
            self._register_row_action_frame(ac.id, unit_id, entry_type, actions)
            self._render_row_actions(actions, ac, unit_id, entry_type, date_str, _sm)

    # -- build a history unit section (generated/finalized) ------------------

    def _build_history_unit_section(self, unit, *, is_schedule: bool):
        """Build interactive absence section for history entries."""
        if is_schedule:
            snap: GeneratedScheduleSlotSnapshot = unit
            label_parts = [f"📋 {snap.description or 'Escala'}"]
            if snap.time:
                label_parts.append(f"({snap.time})")
            label = " ".join(label_parts)
            unit_id = snap.slot_id
            acolyte_ids = snap.acolyte_ids
            entry_type = "schedule"
        else:
            entry = unit
            label_parts = [f"✨ {entry.name}"]
            if entry.time:
                label_parts.append(f"({entry.time})")
            label = " ".join(label_parts)
            unit_id = entry.event_id
            acolyte_ids = entry.participating_acolyte_ids
            entry_type = "event"

        self._register_entry_ref(entry_type, unit_id, unit)

        participants = [ac for ac in self.app.acolytes if ac.id in acolyte_ids]

        lf = ttk.LabelFrame(self._inner, text=label, padding=6)
        lf.pack(fill=tk.X, pady=(0, 6))

        if not participants:
            ttk.Label(lf, text="Nenhum acólito participante.").pack(anchor="w")
            return

        date_str = _format_date(self.day_info.date_obj)
        _sm = ("TkDefaultFont", 8)

        for ac in sorted(participants, key=lambda a: a.name):
            row = ttk.Frame(lf)
            row.pack(fill=tk.X, pady=0)

            display_name = ac.name if len(ac.name) <= 20 else ac.name[:18] + "…"
            name_lbl = ttk.Label(row, text=display_name, width=20, anchor="w", font=_sm)
            name_lbl.pack(side=tk.LEFT)
            actions = ttk.Frame(row)
            actions.pack(side=tk.LEFT)
            self._register_row_action_frame(ac.id, unit_id, entry_type, actions)
            self._render_row_actions(actions, ac, unit_id, entry_type, date_str, _sm)

    # -- absence actions -----------------------------------------------------

    def _add_absence(self, acolyte: Acolyte, unit_id: str,
                     entry_type: str, date_str: str, *, symbolic: bool):
        self._upsert_linked_absence(
            acolyte,
            entry_type,
            unit_id,
            date_str,
            symbolic=symbolic,
        )
        self.app.save()
        self._refresh_acolyte_table_if_needed({acolyte.id})
        self._refresh_row_actions(acolyte, unit_id, entry_type, date_str)

    def _remove_absence(self, acolyte: Acolyte, unit_id: str, date_str: str):
        removed_types = {
            a.linked_entry_type
            for a in acolyte.absences
            if a.date == date_str and a.linked_entry_id == unit_id and a.linked_entry_type
        }
        acolyte.absences = [
            a for a in acolyte.absences
            if not (a.date == date_str and a.linked_entry_id == unit_id)
        ]
        for entry_type in removed_types:
            self._set_linked_missed_flag(acolyte, entry_type, unit_id, False)
        self.app.save()
        self._refresh_acolyte_table_if_needed({acolyte.id})
        for entry_type in ("schedule", "event"):
            self._refresh_row_actions(acolyte, unit_id, entry_type, date_str)

    def _clear_all_absences(self):
        """Remove all absences for every acolyte on this day."""
        date_str = _format_date(self.day_info.date_obj)
        total_removed = 0
        updated_ids = set()
        for ac in self.app.acolytes:
            removed = [a for a in ac.absences if a.date == date_str]
            before = len(ac.absences)
            ac.absences = [a for a in ac.absences if a.date != date_str]
            total_removed += before - len(ac.absences)
            if removed:
                updated_ids.add(ac.id)
            for absence in removed:
                if absence.linked_entry_type and absence.linked_entry_id:
                    self._set_linked_missed_flag(
                        ac, absence.linked_entry_type, absence.linked_entry_id, False
                    )
        if total_removed == 0:
            messagebox.showinfo("Limpar faltas", "Nenhuma falta registrada neste dia.", parent=self)
            return
        self.app.save()
        self._refresh_acolyte_table_if_needed(updated_ids)
        messagebox.showinfo(
            "Limpar faltas",
            f"{total_removed} falta(s) removida(s) do dia {date_str}.",
            parent=self,
        )
        self._refresh_all_row_actions()

    def _quick_absence_all(self, *, symbolic: bool):
        sel_indices = self._quick_ac_listbox.curselection()
        selected_names = [self._quick_ac_sorted[i].name for i in sel_indices]
        if not selected_names:
            messagebox.showwarning("Aviso", "Selecione pelo menos um acólito.", parent=self)
            return

        date_str = _format_date(self.day_info.date_obj)
        total_absences = 0
        updated_ids = set()

        for name in selected_names:
            acolyte = next((ac for ac in self.app.acolytes if ac.name == name), None)
            if acolyte is None:
                continue

            units = []  # (unit_id, entry_type)
            for h_slot in self.day_info.history_slots:
                snap = h_slot["snapshot"]
                if acolyte.id in snap.acolyte_ids:
                    units.append((snap.slot_id, "schedule"))
            for h_evt in self.day_info.history_events:
                entry = h_evt["entry"]
                if acolyte.id in entry.participating_acolyte_ids:
                    units.append((entry.event_id, "event"))

            if not units:
                continue

            unique_units = []
            seen = set()
            for uid, et in units:
                key = (uid, et)
                if key in seen:
                    continue
                seen.add(key)
                unique_units.append((uid, et))

            first = True
            for unit_id, entry_type in unique_units:
                is_sym = (symbolic and not first)
                self._upsert_linked_absence(
                    acolyte,
                    entry_type,
                    unit_id,
                    date_str,
                    symbolic=is_sym,
                )
                first = False
                total_absences += 1

            updated_ids.add(acolyte.id)

        self.app.save()
        self._refresh_acolyte_table_if_needed(updated_ids)
        mode = "1 real + resto simbólica" if symbolic else "todas reais"
        messagebox.showinfo(
            "Faltas Registradas",
            f"{total_absences} falta(s) registrada(s) para {len(selected_names)} acólito(s) ({mode}).",
            parent=self,
        )
        self._refresh_all_row_actions()

    def _rebuild(self):
        """Destroy and rebuild dialog contents, preserving scroll position."""
        scroll_pos = self._canvas.yview()
        for w in self._inner.winfo_children():
            w.destroy()
        self._build_content()
        self._fit_to_content()
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(scroll_pos[0])

    def _build_content(self):
        """Rebuild just the left panel content (called by _rebuild)."""
        self._build_left_content()

    def external_refresh(self):
        """Refresh row actions when data changes externally (e.g. from another tab)."""
        if not self.winfo_exists():
            return
        self._refresh_all_row_actions()


# ---------------------------------------------------------------------------
# Unit Detail Dialog (for timeline view - single unit selection)
# ---------------------------------------------------------------------------

class UnitDetailDialog(tk.Toplevel):
    """Pop-up for a single unit with absence tools."""

    def __init__(self, parent, app, unit, is_schedule: bool, date_obj: date):
        super().__init__(parent)
        self.app = app
        self.unit = unit
        self.is_schedule = is_schedule
        self.date_obj = date_obj
        self._row_action_frames: Dict[str, List[ttk.Frame]] = {}
        self.grab_set()
        self.resizable(True, True)
        self.minsize(420, 200)
        self._set_title()
        self._build()
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

    def _set_title(self):
        if self.is_schedule:
            slot = self.unit
            if getattr(slot, "is_general_event", False):
                name = getattr(slot, "general_event_name", "") or "Escala Geral"
            else:
                name = getattr(slot, "description", "") or "Escala"
            self.title(f"📋 {name} — {_format_date(self.date_obj)}")
        else:
            evt = self.unit
            name = getattr(evt, "name", "") or getattr(evt, "general_event_name", "") or "Atividade"
            self.title(f"✨ {name} — {_format_date(self.date_obj)}")

    def _get_unit_id(self) -> str:
        return (
            getattr(self.unit, "id", "")
            or getattr(self.unit, "slot_id", "")
            or getattr(self.unit, "event_id", "")
        )

    def _get_participants(self) -> List[Acolyte]:
        if self.is_schedule:
            slot = self.unit
            acolyte_ids = list(getattr(slot, "acolyte_ids", []) or [])
            if acolyte_ids:
                return [ac for ac in self.app.acolytes if ac.id in acolyte_ids]
            if getattr(slot, "is_general_event", False):
                excluded = set(getattr(slot, "excluded_acolyte_ids", []) or [])
                return [ac for ac in self.app.acolytes
                        if ac.id not in excluded]
            return []

        evt = self.unit
        participating_ids = list(getattr(evt, "participating_acolyte_ids", []) or [])
        if participating_ids:
            return [ac for ac in self.app.acolytes if ac.id in participating_ids]
        excluded = set(getattr(evt, "excluded_acolyte_ids", []) or [])
        return [ac for ac in self.app.acolytes if ac.id not in excluded]

    def _build(self):
        self._outer = ttk.Frame(self, padding=10)
        self._outer.pack(fill=tk.BOTH, expand=True)
        self._render()

    def _find_absence(self, acolyte: Acolyte, unit_id: str, date_str: str) -> Optional[Absence]:
        return next(
            (
                a
                for a in acolyte.absences
                if a.date == date_str and a.linked_entry_id == unit_id
            ),
            None,
        )

    def _register_row_action_frame(self, acolyte_id: str, frame: ttk.Frame):
        self._row_action_frames.setdefault(acolyte_id, []).append(frame)

    def _render_row_actions(
        self,
        action_frame: ttk.Frame,
        acolyte: Acolyte,
        unit_id: str,
        entry_type: str,
        date_str: str,
    ):
        for widget in action_frame.winfo_children():
            widget.destroy()

        absence_obj = self._find_absence(acolyte, unit_id, date_str)
        if absence_obj:
            kind = "simb." if absence_obj.is_symbolic else "real"
            ttk.Button(
                action_frame,
                text="Remover",
                command=lambda a=acolyte, uid=unit_id, ds=date_str: self._remove_absence(a, uid, ds),
            ).pack(side=tk.RIGHT, padx=2)
            ttk.Label(
                action_frame,
                text=f"✗ Falta ({kind})",
                foreground="red",
            ).pack(side=tk.RIGHT, padx=4)
            return

        ttk.Button(
            action_frame,
            text="Real",
            command=lambda a=acolyte, uid=unit_id, et=entry_type, ds=date_str: (
                self._add_absence(a, uid, et, ds, symbolic=False)
            ),
        ).pack(side=tk.RIGHT, padx=2)
        ttk.Button(
            action_frame,
            text="Simb.",
            command=lambda a=acolyte, uid=unit_id, et=entry_type, ds=date_str: (
                self._add_absence(a, uid, et, ds, symbolic=True)
            ),
        ).pack(side=tk.RIGHT, padx=2)

    def _refresh_row_actions(self, acolyte: Acolyte):
        date_str = _format_date(self.date_obj)
        unit_id = self._get_unit_id()
        entry_type = "schedule" if self.is_schedule else "event"
        for frame in self._row_action_frames.get(acolyte.id, []):
            self._render_row_actions(frame, acolyte, unit_id, entry_type, date_str)

    def _refresh_all_row_actions(self):
        acolytes_by_id = {ac.id: ac for ac in self.app.acolytes}
        date_str = _format_date(self.date_obj)
        unit_id = self._get_unit_id()
        entry_type = "schedule" if self.is_schedule else "event"
        for acolyte_id, frames in self._row_action_frames.items():
            acolyte = acolytes_by_id.get(acolyte_id)
            if acolyte is None:
                continue
            for frame in frames:
                self._render_row_actions(frame, acolyte, unit_id, entry_type, date_str)

    def _render(self):
        for w in self._outer.winfo_children():
            w.destroy()
        self._row_action_frames = {}

        participants = self._get_participants()
        date_str = _format_date(self.date_obj)
        unit_id = self._get_unit_id()
        entry_type = "schedule" if self.is_schedule else "event"

        if not participants:
            ttk.Label(self._outer, text="Nenhum acólito participante.").pack(anchor="w")
            ttk.Button(self._outer, text="Fechar", command=self.destroy).pack(pady=8)
            return

        ttk.Label(
            self._outer,
            text=f"Participantes ({len(participants)}):",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        for ac in sorted(participants, key=lambda a: a.name):
            row = ttk.Frame(self._outer)
            row.pack(fill=tk.X, pady=1)

            ttk.Label(row, text=ac.name, width=25, anchor="w").pack(side=tk.LEFT)
            actions = ttk.Frame(row)
            actions.pack(side=tk.RIGHT)
            self._register_row_action_frame(ac.id, actions)
            self._render_row_actions(actions, ac, unit_id, entry_type, date_str)

        ttk.Button(self._outer, text="Fechar", command=self.destroy).pack(pady=8)

    def _build_linked_absence_description(self, entry_type: str, date_str: str) -> str:
        label = "atividade" if entry_type == "event" else "escala"
        if entry_type == "event":
            detail = getattr(self.unit, "name", "") or "Sem descrição"
        else:
            detail = (
                getattr(self.unit, "description", "")
                or getattr(self.unit, "general_event_name", "")
                or "Sem descrição"
            )
        time_str = getattr(self.unit, "time", "") or "-"
        return f"Faltou {label}: {detail} {date_str} {time_str}"

    def _set_linked_missed_flag(self, acolyte: Acolyte, entry_type: str, entry_id: str, missed: bool):
        if entry_type == "schedule":
            found = False
            for entry in acolyte.schedule_history:
                if entry.schedule_id == entry_id:
                    entry.missed = missed
                    found = True
            if not found and missed:
                date_str = _format_date(self.date_obj)
                acolyte.schedule_history.append(
                    ScheduleHistoryEntry(
                        schedule_id=entry_id,
                        date=date_str,
                        day=detect_weekday(date_str),
                        time=getattr(self.unit, "time", "") or "",
                        description=(
                            getattr(self.unit, "description", "")
                            or getattr(self.unit, "general_event_name", "")
                            or ""
                        ),
                        missed=True,
                    )
                )
            return

        found = False
        for entry in acolyte.event_history:
            if entry.event_id == entry_id:
                entry.missed = missed
                found = True
        if not found and missed:
            date_str = _format_date(self.date_obj)
            acolyte.event_history.append(
                EventHistoryEntry(
                    event_id=entry_id,
                    name=getattr(self.unit, "name", "") or "Atividade",
                    date=date_str,
                    time=getattr(self.unit, "time", "") or "",
                    missed=True,
                )
            )

    def _refresh_acolyte_table_if_needed(self, updated_acolyte_ids: set):
        ac_tab = getattr(self.app, "acolytes_tab", None)
        if ac_tab is None:
            return
        ac_tab.refresh_list()
        current = getattr(ac_tab, "_current_acolyte", None)
        if current and current.id in updated_acolyte_ids:
            ac_tab._show_acolyte_detail()

    def _add_absence(self, acolyte: Acolyte, unit_id: str,
                     entry_type: str, date_str: str, *, symbolic: bool):
        existing = next(
            (a for a in acolyte.absences if a.date == date_str and a.linked_entry_id == unit_id),
            None,
        )
        description = self._build_linked_absence_description(entry_type, date_str)
        if existing:
            existing.description = description
            existing.linked_entry_type = entry_type
            existing.linked_entry_id = unit_id
            existing.is_symbolic = symbolic
        else:
            acolyte.absences.append(
                Absence(
                    date=date_str,
                    description=description,
                    linked_entry_type=entry_type,
                    linked_entry_id=unit_id,
                    is_symbolic=symbolic,
                )
            )

        self._set_linked_missed_flag(acolyte, entry_type, unit_id, True)
        self.app.save()
        self._refresh_acolyte_table_if_needed({acolyte.id})
        self._refresh_row_actions(acolyte)

    def _remove_absence(self, acolyte: Acolyte, unit_id: str, date_str: str):
        removed_types = {
            a.linked_entry_type
            for a in acolyte.absences
            if a.date == date_str and a.linked_entry_id == unit_id and a.linked_entry_type
        }
        acolyte.absences = [
            a for a in acolyte.absences
            if not (a.date == date_str and a.linked_entry_id == unit_id)
        ]
        for entry_type in removed_types:
            self._set_linked_missed_flag(acolyte, entry_type, unit_id, False)
        self.app.save()
        self._refresh_acolyte_table_if_needed({acolyte.id})
        self._refresh_row_actions(acolyte)

    def external_refresh(self):
        """Refresh dialog rows when data changes externally (e.g. from another tab)."""
        if not self.winfo_exists():
            return
        self._refresh_all_row_actions()


# ---------------------------------------------------------------------------
# CalendarTab
# ---------------------------------------------------------------------------

class CalendarTab(ttk.Frame):
    """Aba de calendário com visualizações mensal e linha do tempo."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._view_year = datetime.now().year
        self._view_month = datetime.now().month
        self._open_day_dialogs: List[DayDetailDialog] = []
        self._open_unit_dialogs: List[UnitDetailDialog] = []
        self._build()

    # -- public API ----------------------------------------------------------

    def refresh(self):
        """Refresh both views."""
        self._draw_calendar()
        self._refresh_timeline()

    def refresh_open_dialogs(self):
        """Refresh currently-open day/unit dialogs to reflect external changes."""
        self._open_day_dialogs = [dlg for dlg in self._open_day_dialogs if dlg.winfo_exists()]
        self._open_unit_dialogs = [dlg for dlg in self._open_unit_dialogs if dlg.winfo_exists()]

        for dlg in self._open_day_dialogs:
            dlg.external_refresh()
        for dlg in self._open_unit_dialogs:
            dlg.external_refresh()

        self._draw_calendar()
        self._refresh_timeline()

    # -- build ---------------------------------------------------------------

    def _build(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # -- Calendar view ---------------------------------------------------
        cal_frame = ttk.Frame(self._notebook)
        self._notebook.add(cal_frame, text="📅 Datas")

        nav = ttk.Frame(cal_frame)
        nav.pack(fill=tk.X, pady=6, padx=10)

        ttk.Button(nav, text="◀◀", width=4,
                   command=self._prev_year).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav, text="◀", width=3,
                   command=self._prev_month).pack(side=tk.LEFT)
        self._month_label = ttk.Label(
            nav, text="", width=24, anchor="center",
            font=("TkDefaultFont", 12, "bold"),
        )
        self._month_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(nav, text="Hoje", command=self._go_today).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav, text="▶▶", width=4,
                   command=self._next_year).pack(side=tk.RIGHT, padx=2)
        ttk.Button(nav, text="▶", width=3,
                   command=self._next_month).pack(side=tk.RIGHT)

        # Legend
        legend = ttk.Frame(cal_frame)
        legend.pack(pady=(0, 4))
        tk.Label(legend, text="  ", bg="#4A90E2", width=3).pack(side=tk.LEFT, padx=2)
        ttk.Label(legend, text="Hoje").pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(legend, text="  ", bg="#E8A838", width=3).pack(side=tk.LEFT, padx=2)
        ttk.Label(legend, text="Com evento").pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(legend, text="  ", bg="#5BB85D", width=3).pack(side=tk.LEFT, padx=2)
        ttk.Label(legend, text="Hoje + evento").pack(side=tk.LEFT)

        self._cal_frame = ttk.Frame(cal_frame)
        self._cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self._draw_calendar()

        # -- Timeline view ---------------------------------------------------
        tl_frame = ttk.Frame(self._notebook)
        self._notebook.add(tl_frame, text="📜 Linha do Tempo")

        # Scrollable timeline
        tl_scroll = ttk.Frame(tl_frame)
        tl_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        tl_canvas = tk.Canvas(tl_scroll, highlightthickness=0)
        tl_vscroll = ttk.Scrollbar(tl_scroll, orient=tk.VERTICAL, command=tl_canvas.yview)
        tl_canvas.configure(yscrollcommand=tl_vscroll.set)
        tl_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        tl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tl_inner = ttk.Frame(tl_canvas)
        self._tl_canvas_window = tl_canvas.create_window(
            (0, 0), window=self._tl_inner, anchor="nw"
        )
        self._tl_canvas = tl_canvas

        def _on_tl_configure(_evt):
            tl_canvas.configure(scrollregion=tl_canvas.bbox("all"))
        self._tl_inner.bind("<Configure>", _on_tl_configure)

        def _on_tl_canvas_configure(event):
            tl_canvas.itemconfigure(self._tl_canvas_window, width=event.width)
        tl_canvas.bind("<Configure>", _on_tl_canvas_configure)

        def _on_tl_mousewheel(event):
            tl_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        tl_canvas.bind("<MouseWheel>", _on_tl_mousewheel)

        self._refresh_timeline()

        # Auto-refresh when switching sub-tabs
        self._notebook.bind("<<NotebookTabChanged>>", lambda _e: self.refresh())

    # -- data gathering ------------------------------------------------------

    def _get_day_infos_for_month(self, year: int, month: int) -> Dict[int, DayInfo]:
        """Build a mapping of day-of-month -> DayInfo for the given month.

        IMPORTANT: planning drafts from `schedule_slots` and `general_events` are
        intentionally ignored here. Only finalized/history entries are shown in
        Calendar/Timeline to avoid registering absences for drafts.
        """
        import calendar as _cal
        num_days = _cal.monthrange(year, month)[1]
        infos: Dict[int, DayInfo] = {}

        for day_num in range(1, num_days + 1):
            infos[day_num] = DayInfo(date(year, month, day_num))

        date_format = "%d/%m/%Y"

        # Birthdays
        for ac in self.app.acolytes:
            if not ac.birthdate:
                continue
            for day_num in range(1, num_days + 1):
                if _birthdate_matches_day(ac.birthdate, day_num, month):
                    infos[day_num].birthdays.append(ac)

        # Generated schedules (history)
        for gs in self.app.generated_schedules:
            for snap in gs.slots:
                d = _parse_date(snap.date)
                if d and d.year == year and d.month == month and d.day in infos:
                    infos[d.day].history_slots.append({
                        "snapshot": snap,
                        "schedule": gs,
                    })

        # Finalized event batches (history)
        for fb in self.app.finalized_event_batches:
            for entry in fb.entries:
                d = _parse_date(entry.date)
                if d and d.year == year and d.month == month and d.day in infos:
                    infos[d.day].history_events.append({
                        "entry": entry,
                        "batch": fb,
                    })

        return infos

    def _get_all_timeline_entries(self) -> List[dict]:
        """Build a flat list of timeline entries, sorted newest first.

        IMPORTANT: only finalized/history entries appear here. Draft planning
        cards (`schedule_slots` / `general_events`) are intentionally excluded.
        """
        entries = []

        # Generated schedules (history)
        for gs in self.app.generated_schedules:
            for snap in gs.slots:
                d = _parse_date(snap.date)
                if not d:
                    continue
                if snap.is_general_event:
                    name = snap.description or "Escala Geral"
                else:
                    name = snap.description or "Escala"
                label = f"📋 {name}"
                if snap.time:
                    label += f" ({snap.time})"
                count = len(snap.acolyte_ids)
                entries.append({
                    "date": d,
                    "label": label,
                    "type": "history_schedule",
                    "unit": snap,
                    "is_schedule": True,
                    "count": count,
                })

        # Finalized event batches (history)
        for fb in self.app.finalized_event_batches:
            for entry in fb.entries:
                d = _parse_date(entry.date)
                if not d:
                    continue
                label = f"✨ {entry.name}"
                if entry.time:
                    label += f" ({entry.time})"
                count = len(entry.participating_acolyte_ids)
                entries.append({
                    "date": d,
                    "label": label,
                    "type": "history_event",
                    "unit": entry,
                    "is_schedule": False,
                    "count": count,
                })

        # Birthdays
        for ac in self.app.acolytes:
            if not ac.birthdate:
                continue
            d = _parse_date(ac.birthdate)
            if not d:
                continue
            try:
                d_this_year = d.replace(year=datetime.now().year)
            except ValueError:
                continue
            entries.append({
                "date": d_this_year,
                "label": f"🎂 Aniversário — {ac.name}",
                "type": "birthday",
                "unit": None,
                "is_schedule": False,
                "count": 0,
                "acolyte": ac,
            })

        def _timeline_sort_key(entry: dict):
            d = entry["date"]
            unit = entry.get("unit")
            time_str = ""
            if unit is not None:
                time_str = (getattr(unit, "time", "") or "").strip()

            # Same-date order: no time first, then timed entries from latest to earliest.
            if not time_str:
                time_group = 0
                time_order = 0
            else:
                try:
                    hh, mm = time_str.split(":", 1)
                    minutes = int(hh) * 60 + int(mm)
                    time_group = 1
                    time_order = -minutes
                except (ValueError, TypeError):
                    time_group = 1
                    time_order = 0

            # Primary order remains newest date first.
            return (-d.toordinal(), time_group, time_order, entry.get("label", ""))

        entries.sort(key=_timeline_sort_key)
        return entries

    # -- calendar drawing ----------------------------------------------------

    def _draw_calendar(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        self._month_label.config(
            text=f"{_MONTH_NAMES[self._view_month - 1]} {self._view_year}"
        )

        day_infos = self._get_day_infos_for_month(self._view_year, self._view_month)

        today = datetime.now().date()
        is_current_month = (today.month == self._view_month and today.year == self._view_year)
        today_day = today.day if is_current_month else None

        # Day headers
        for col, name in enumerate(_DAY_HEADERS):
            ttk.Label(
                self._cal_frame, text=name, width=14, anchor="center",
                font=("TkDefaultFont", 9, "bold"),
            ).grid(row=0, column=col, padx=2, pady=2)

        weeks = cal_module.monthcalendar(self._view_year, self._view_month)
        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self._cal_frame, text="", width=14).grid(
                        row=r + 1, column=c, padx=2, pady=2
                    )
                    continue

                is_today = (day == today_day)
                info = day_infos.get(day)
                has_content = info.has_content if info else False

                # Determine styling
                if is_today and has_content:
                    bg = "#5BB85D"
                    fg = "white"
                    font = ("TkDefaultFont", 9, "bold")
                elif is_today:
                    bg = "#4A90E2"
                    fg = "white"
                    font = ("TkDefaultFont", 9, "bold")
                elif has_content:
                    bg = "#E8A838"
                    fg = "white"
                    font = ("TkDefaultFont", 9, "bold")
                else:
                    bg = None
                    fg = None
                    font = ("TkDefaultFont", 9)

                # Build cell text
                text = str(day)
                if info and info.has_content:
                    indicators = []
                    if info.birthdays:
                        indicators.append("🎂")
                    if info.schedule_slots or info.history_slots:
                        indicators.append("📋")
                    if info.general_events or info.history_events:
                        indicators.append("✨")
                    text += "\n" + " ".join(indicators)

                if bg:
                    btn = tk.Button(
                        self._cal_frame,
                        text=text,
                        width=12,
                        height=3,
                        command=lambda d=day: self._on_day_click(d),
                        bg=bg,
                        fg=fg,
                        font=font,
                        relief=tk.RAISED,
                        cursor="hand2",
                        anchor="center",
                        justify="center",
                    )
                else:
                    btn = tk.Button(
                        self._cal_frame,
                        text=text,
                        width=12,
                        height=3,
                        command=lambda d=day: self._on_day_click(d),
                        font=font,
                        relief=tk.GROOVE,
                        cursor="hand2",
                        anchor="center",
                        justify="center",
                    )
                btn.grid(row=r + 1, column=c, padx=2, pady=2, sticky="nsew")

        # Make grid cells expand
        for c in range(7):
            self._cal_frame.columnconfigure(c, weight=1)
        for r in range(len(weeks) + 1):
            self._cal_frame.rowconfigure(r, weight=1)

    # -- timeline drawing ----------------------------------------------------

    def _refresh_timeline(self):
        for w in self._tl_inner.winfo_children():
            w.destroy()

        entries = self._get_all_timeline_entries()
        today = datetime.now().date()

        if not entries:
            ttk.Label(
                self._tl_inner,
                text="Nenhum evento encontrado.",
                font=("TkDefaultFont", 10),
            ).pack(pady=20)
            return

        current_date_str = None
        for entry in entries:
            d: date = entry["date"]
            date_label = _format_date(d)

            # Date header (group by date)
            if date_label != current_date_str:
                current_date_str = date_label
                is_today = (d == today)
                weekday = detect_weekday(date_label)

                hdr = ttk.Frame(self._tl_inner)
                hdr.pack(fill=tk.X, pady=(10, 2))

                if is_today:
                    lbl = tk.Label(
                        hdr, text=f"📌 {date_label} - {weekday} (Hoje)",
                        font=("TkDefaultFont", 11, "bold"),
                        bg="#4A90E2", fg="white",
                        padx=8, pady=2,
                    )
                else:
                    lbl = ttk.Label(
                        hdr, text=f"📅 {date_label} - {weekday}",
                        font=("TkDefaultFont", 11, "bold"),
                    )
                lbl.pack(anchor="w")
                ttk.Separator(self._tl_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

            # Entry row
            row = ttk.Frame(self._tl_inner)
            row.pack(fill=tk.X, padx=10, pady=2)

            ttk.Label(row, text=entry["label"], font=("TkDefaultFont", 10)).pack(
                side=tk.LEFT
            )

            if entry["type"] != "birthday":
                count = entry["count"]
                ttk.Label(
                    row, text=f"({count} acólito{'s' if count != 1 else ''})",
                    foreground="gray",
                ).pack(side=tk.LEFT, padx=6)

                if entry["type"] in ("history_schedule", "history_event"):
                    ttk.Button(
                        row, text="Faltas",
                        command=lambda e=entry: self._open_unit_detail(e),
                    ).pack(side=tk.RIGHT, padx=2)

    # -- event handlers ------------------------------------------------------

    def _on_day_click(self, day: int):
        day_infos = self._get_day_infos_for_month(self._view_year, self._view_month)
        info = day_infos.get(day)
        if info is None:
            return
        dlg = DayDetailDialog(self, self.app, info)
        self._open_day_dialogs.append(dlg)
        dlg.bind(
            "<Destroy>",
            lambda _e, d=dlg: self._open_day_dialogs.remove(d) if d in self._open_day_dialogs else None,
            add="+",
        )

    def _open_unit_detail(self, entry: dict):
        dlg = UnitDetailDialog(
            self, self.app,
            unit=entry["unit"],
            is_schedule=entry["is_schedule"],
            date_obj=entry["date"],
        )
        self._open_unit_dialogs.append(dlg)
        dlg.bind(
            "<Destroy>",
            lambda _e, d=dlg: self._open_unit_dialogs.remove(d) if d in self._open_unit_dialogs else None,
            add="+",
        )

    # -- navigation ----------------------------------------------------------

    def _prev_month(self):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._draw_calendar()

    def _next_month(self):
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._draw_calendar()

    def _prev_year(self):
        self._view_year -= 1
        self._draw_calendar()

    def _next_year(self):
        self._view_year += 1
        self._draw_calendar()

    def _go_today(self):
        now = datetime.now()
        self._view_year = now.year
        self._view_month = now.month
        self._draw_calendar()
