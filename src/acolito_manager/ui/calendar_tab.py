"""Aba de calendário com visualização mensal e linha do tempo."""

import calendar as cal_module
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import List, Dict, Optional

from ..models import Absence, ScheduleSlot, GeneralEvent, Acolyte


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

    __slots__ = ("date_obj", "birthdays", "schedule_slots", "general_events")

    def __init__(self, date_obj: date):
        self.date_obj = date_obj
        self.birthdays: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []

    @property
    def has_content(self) -> bool:
        return bool(self.birthdays or self.schedule_slots or self.general_events)


# ---------------------------------------------------------------------------
# Day Detail Dialog (shown when user clicks a day)
# ---------------------------------------------------------------------------

class DayDetailDialog(tk.Toplevel):
    """Pop-up showing details and absence tools for a specific day."""

    def __init__(self, parent, app, day_info: DayInfo):
        super().__init__(parent)
        self.app = app
        self.day_info = day_info
        self.title(f"📅 {_format_date(day_info.date_obj)}")
        self.resizable(True, True)
        self.minsize(480, 300)
        self.grab_set()
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

    # -- build ---------------------------------------------------------------

    def _build(self):
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        # Scrollable canvas
        canvas = tk.Canvas(outer, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = ttk.Frame(canvas)
        self._canvas_win_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        def _on_configure(_evt):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._inner.bind("<Configure>", _on_configure)

        def _on_canvas_resize(event):
            canvas.itemconfigure(self._canvas_win_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        self.bind("<Destroy>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        date_str = _format_date(self.day_info.date_obj)

        # -- Birthdays -------------------------------------------------------
        if self.day_info.birthdays:
            lf = ttk.LabelFrame(self._inner, text="🎂 Aniversariantes", padding=6)
            lf.pack(fill=tk.X, pady=(0, 6))
            for ac in self.day_info.birthdays:
                ttk.Label(lf, text=f"• {ac.name}").pack(anchor="w")

        # -- Quick tool: mark acolyte absent in ALL units this day -----------
        all_acolytes_in_day = self._get_all_acolytes_in_day()
        if all_acolytes_in_day:
            lf = ttk.LabelFrame(
                self._inner,
                text="⚡ Falta rápida — marcar acólito ausente em todas as unidades",
                padding=6,
            )
            lf.pack(fill=tk.X, pady=(0, 6))

            ttk.Label(lf, text="Acólito:").pack(anchor="w")
            self._quick_ac_var = tk.StringVar()
            ac_names = sorted(ac.name for ac in all_acolytes_in_day)
            combo = ttk.Combobox(lf, textvariable=self._quick_ac_var,
                                 values=ac_names, state="readonly", width=30)
            combo.pack(anchor="w", pady=2)

            btn_frame = ttk.Frame(lf)
            btn_frame.pack(anchor="w", pady=4)
            ttk.Button(
                btn_frame, text="Tudo como falta real",
                command=lambda: self._quick_absence_all(symbolic=False),
            ).pack(side=tk.LEFT, padx=(0, 4))
            ttk.Button(
                btn_frame, text="1 real + resto simbólica",
                command=lambda: self._quick_absence_all(symbolic=True),
            ).pack(side=tk.LEFT)

        # -- Per-unit sections -----------------------------------------------
        for slot in self.day_info.schedule_slots:
            self._build_unit_section(slot, is_schedule=True)

        for evt in self.day_info.general_events:
            self._build_unit_section(evt, is_schedule=False)

        # -- Close button ----------------------------------------------------
        ttk.Button(self._inner, text="Fechar", command=self.destroy).pack(pady=8)

    # -- helpers -------------------------------------------------------------

    def _get_all_acolytes_in_day(self) -> List[Acolyte]:
        """Return deduplicated list of acolytes participating in any unit this day."""
        ids = set()
        for slot in self.day_info.schedule_slots:
            if slot.is_general_event:
                for ac in self.app.acolytes:
                    if ac.id not in slot.excluded_acolyte_ids:
                        ids.add(ac.id)
            else:
                ids.update(slot.acolyte_ids)
        for evt in self.day_info.general_events:
            for ac in self.app.acolytes:
                if ac.id not in evt.excluded_acolyte_ids:
                    ids.add(ac.id)
        return [ac for ac in self.app.acolytes if ac.id in ids]

    def _get_participants(self, unit, is_schedule: bool) -> List[Acolyte]:
        if is_schedule:
            slot: ScheduleSlot = unit
            if slot.is_general_event:
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

    # -- build a single unit section -----------------------------------------

    def _build_unit_section(self, unit, *, is_schedule: bool):
        label = self._unit_label(unit, is_schedule)
        participants = self._get_participants(unit, is_schedule)

        lf = ttk.LabelFrame(self._inner, text=label, padding=6)
        lf.pack(fill=tk.X, pady=(0, 6))

        if not participants:
            ttk.Label(lf, text="Nenhum acólito participante.").pack(anchor="w")
            return

        date_str = _format_date(self.day_info.date_obj)
        unit_id = unit.id

        # For each participant, a row with name + absence buttons
        for ac in sorted(participants, key=lambda a: a.name):
            row = ttk.Frame(lf)
            row.pack(fill=tk.X, pady=1)

            ttk.Label(row, text=ac.name, width=25, anchor="w").pack(side=tk.LEFT)

            entry_type = "schedule" if is_schedule else "event"

            # Check if already has absence for this unit on this day
            has_absence = any(
                a.date == date_str and a.linked_entry_id == unit_id
                for a in ac.absences
            )
            if has_absence:
                ttk.Label(row, text="✗ Falta registrada", foreground="red").pack(
                    side=tk.LEFT, padx=4
                )
                ttk.Button(
                    row, text="Remover",
                    command=lambda a=ac, uid=unit_id, ds=date_str: self._remove_absence(
                        a, uid, ds
                    ),
                ).pack(side=tk.LEFT, padx=2)
            else:
                ttk.Button(
                    row, text="Falta real",
                    command=lambda a=ac, uid=unit_id, et=entry_type, ds=date_str: (
                        self._add_absence(a, uid, et, ds, symbolic=False)
                    ),
                ).pack(side=tk.LEFT, padx=2)
                ttk.Button(
                    row, text="Simbólica",
                    command=lambda a=ac, uid=unit_id, et=entry_type, ds=date_str: (
                        self._add_absence(a, uid, et, ds, symbolic=True)
                    ),
                ).pack(side=tk.LEFT, padx=2)

    # -- absence actions -----------------------------------------------------

    def _add_absence(self, acolyte: Acolyte, unit_id: str,
                     entry_type: str, date_str: str, *, symbolic: bool):
        absence = Absence(
            date=date_str,
            description=f"Registrada via calendário",
            linked_entry_type=entry_type,
            linked_entry_id=unit_id,
            is_symbolic=symbolic,
        )
        acolyte.absences.append(absence)
        self.app.save()
        self._rebuild()

    def _remove_absence(self, acolyte: Acolyte, unit_id: str, date_str: str):
        acolyte.absences = [
            a for a in acolyte.absences
            if not (a.date == date_str and a.linked_entry_id == unit_id)
        ]
        self.app.save()
        self._rebuild()

    def _quick_absence_all(self, *, symbolic: bool):
        name = self._quick_ac_var.get()
        if not name:
            messagebox.showwarning("Aviso", "Selecione um acólito.", parent=self)
            return
        acolyte = next((ac for ac in self.app.acolytes if ac.name == name), None)
        if acolyte is None:
            return

        date_str = _format_date(self.day_info.date_obj)
        units = []  # (unit_id, entry_type)
        for slot in self.day_info.schedule_slots:
            participants = self._get_participants(slot, is_schedule=True)
            if any(p.id == acolyte.id for p in participants):
                units.append((slot.id, "schedule"))
        for evt in self.day_info.general_events:
            participants = self._get_participants(evt, is_schedule=False)
            if any(p.id == acolyte.id for p in participants):
                units.append((evt.id, "event"))

        if not units:
            messagebox.showinfo(
                "Info", f"{name} não participa de nenhuma unidade neste dia.",
                parent=self,
            )
            return

        # Remove pre-existing absences for these units on this date
        existing_ids = {uid for uid, _ in units}
        acolyte.absences = [
            a for a in acolyte.absences
            if not (a.date == date_str and a.linked_entry_id in existing_ids)
        ]

        first = True
        for unit_id, entry_type in units:
            # "1 real + rest symbolic": first unit is real, remainder symbolic
            is_sym = (symbolic and not first)

            absence = Absence(
                date=date_str,
                description="Registrada via calendário (rápida)",
                linked_entry_type=entry_type,
                linked_entry_id=unit_id,
                is_symbolic=is_sym,
            )
            acolyte.absences.append(absence)
            first = False

        self.app.save()
        total = len(units)
        mode = "1 real + resto simbólica" if symbolic else "todas reais"
        messagebox.showinfo(
            "Faltas Registradas",
            f"{total} falta(s) registrada(s) para {name} ({mode}).",
            parent=self,
        )
        self._rebuild()

    def _rebuild(self):
        """Destroy and rebuild dialog contents."""
        for w in self._inner.winfo_children():
            w.destroy()
        self._build_content()

    def _build_content(self):
        """Rebuild just the inner content (called by _rebuild)."""
        date_str = _format_date(self.day_info.date_obj)

        if self.day_info.birthdays:
            lf = ttk.LabelFrame(self._inner, text="🎂 Aniversariantes", padding=6)
            lf.pack(fill=tk.X, pady=(0, 6))
            for ac in self.day_info.birthdays:
                ttk.Label(lf, text=f"• {ac.name}").pack(anchor="w")

        all_acolytes_in_day = self._get_all_acolytes_in_day()
        if all_acolytes_in_day:
            lf = ttk.LabelFrame(
                self._inner,
                text="⚡ Falta rápida — marcar acólito ausente em todas as unidades",
                padding=6,
            )
            lf.pack(fill=tk.X, pady=(0, 6))
            ttk.Label(lf, text="Acólito:").pack(anchor="w")
            self._quick_ac_var = tk.StringVar()
            ac_names = sorted(ac.name for ac in all_acolytes_in_day)
            combo = ttk.Combobox(lf, textvariable=self._quick_ac_var,
                                 values=ac_names, state="readonly", width=30)
            combo.pack(anchor="w", pady=2)
            btn_frame = ttk.Frame(lf)
            btn_frame.pack(anchor="w", pady=4)
            ttk.Button(
                btn_frame, text="Tudo como falta real",
                command=lambda: self._quick_absence_all(symbolic=False),
            ).pack(side=tk.LEFT, padx=(0, 4))
            ttk.Button(
                btn_frame, text="1 real + resto simbólica",
                command=lambda: self._quick_absence_all(symbolic=True),
            ).pack(side=tk.LEFT)

        for slot in self.day_info.schedule_slots:
            self._build_unit_section(slot, is_schedule=True)
        for evt in self.day_info.general_events:
            self._build_unit_section(evt, is_schedule=False)

        ttk.Button(self._inner, text="Fechar", command=self.destroy).pack(pady=8)


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
            slot: ScheduleSlot = self.unit
            if slot.is_general_event:
                name = slot.general_event_name or "Escala Geral"
            else:
                name = slot.description or "Escala"
            self.title(f"📋 {name} — {_format_date(self.date_obj)}")
        else:
            evt: GeneralEvent = self.unit
            self.title(f"✨ {evt.name} — {_format_date(self.date_obj)}")

    def _get_participants(self) -> List[Acolyte]:
        if self.is_schedule:
            slot: ScheduleSlot = self.unit
            if slot.is_general_event:
                return [ac for ac in self.app.acolytes
                        if ac.id not in slot.excluded_acolyte_ids]
            return [ac for ac in self.app.acolytes if ac.id in slot.acolyte_ids]
        else:
            evt: GeneralEvent = self.unit
            return [ac for ac in self.app.acolytes
                    if ac.id not in evt.excluded_acolyte_ids]

    def _build(self):
        self._outer = ttk.Frame(self, padding=10)
        self._outer.pack(fill=tk.BOTH, expand=True)
        self._render()

    def _render(self):
        for w in self._outer.winfo_children():
            w.destroy()

        participants = self._get_participants()
        date_str = _format_date(self.date_obj)
        unit_id = self.unit.id
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

            has_absence = any(
                a.date == date_str and a.linked_entry_id == unit_id
                for a in ac.absences
            )
            if has_absence:
                ttk.Label(row, text="✗ Falta registrada", foreground="red").pack(
                    side=tk.LEFT, padx=4
                )
                ttk.Button(
                    row, text="Remover",
                    command=lambda a=ac, uid=unit_id, ds=date_str: self._remove_absence(
                        a, uid, ds
                    ),
                ).pack(side=tk.LEFT, padx=2)
            else:
                ttk.Button(
                    row, text="Falta real",
                    command=lambda a=ac, uid=unit_id, et=entry_type, ds=date_str: (
                        self._add_absence(a, uid, et, ds, symbolic=False)
                    ),
                ).pack(side=tk.LEFT, padx=2)
                ttk.Button(
                    row, text="Simbólica",
                    command=lambda a=ac, uid=unit_id, et=entry_type, ds=date_str: (
                        self._add_absence(a, uid, et, ds, symbolic=True)
                    ),
                ).pack(side=tk.LEFT, padx=2)

        ttk.Button(self._outer, text="Fechar", command=self.destroy).pack(pady=8)

    def _add_absence(self, acolyte: Acolyte, unit_id: str,
                     entry_type: str, date_str: str, *, symbolic: bool):
        absence = Absence(
            date=date_str,
            description="Registrada via calendário",
            linked_entry_type=entry_type,
            linked_entry_id=unit_id,
            is_symbolic=symbolic,
        )
        acolyte.absences.append(absence)
        self.app.save()
        self._render()

    def _remove_absence(self, acolyte: Acolyte, unit_id: str, date_str: str):
        acolyte.absences = [
            a for a in acolyte.absences
            if not (a.date == date_str and a.linked_entry_id == unit_id)
        ]
        self.app.save()
        self._render()


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
        self._build()

    # -- public API ----------------------------------------------------------

    def refresh(self):
        """Refresh both views."""
        self._draw_calendar()
        self._refresh_timeline()

    # -- build ---------------------------------------------------------------

    def _build(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # -- Calendar view ---------------------------------------------------
        cal_frame = ttk.Frame(self._notebook)
        self._notebook.add(cal_frame, text="📅 Calendário")

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
        ttk.Button(nav, text="▶", width=3,
                   command=self._next_month).pack(side=tk.RIGHT)
        ttk.Button(nav, text="▶▶", width=4,
                   command=self._next_year).pack(side=tk.RIGHT, padx=2)

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

        tl_top = ttk.Frame(tl_frame)
        tl_top.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(tl_top, text="🔄 Atualizar",
                   command=self._refresh_timeline).pack(side=tk.LEFT)

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

    # -- data gathering ------------------------------------------------------

    def _get_day_infos_for_month(self, year: int, month: int) -> Dict[int, DayInfo]:
        """Build a mapping of day-of-month -> DayInfo for the given month."""
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

        # Schedule slots
        for slot in self.app.schedule_slots:
            d = _parse_date(slot.date)
            if d and d.year == year and d.month == month and d.day in infos:
                infos[d.day].schedule_slots.append(slot)

        # General events
        for evt in self.app.general_events:
            d = _parse_date(evt.date)
            if d and d.year == year and d.month == month and d.day in infos:
                infos[d.day].general_events.append(evt)

        return infos

    def _get_all_timeline_entries(self) -> List[dict]:
        """Build a flat list of timeline entries, sorted newest first."""
        entries = []

        for slot in self.app.schedule_slots:
            d = _parse_date(slot.date)
            if not d:
                continue
            if slot.is_general_event:
                name = slot.general_event_name or "Escala Geral"
            else:
                name = slot.description or "Escala"
            label = f"📋 {name}"
            if slot.time:
                label += f" ({slot.time})"
            # Count participants
            if slot.is_general_event:
                count = sum(
                    1 for ac in self.app.acolytes
                    if ac.id not in slot.excluded_acolyte_ids
                )
            else:
                count = len(slot.acolyte_ids)
            entries.append({
                "date": d,
                "label": label,
                "type": "schedule",
                "unit": slot,
                "is_schedule": True,
                "count": count,
            })

        for evt in self.app.general_events:
            d = _parse_date(evt.date)
            if not d:
                continue
            label = f"✨ {evt.name}"
            if evt.time:
                label += f" ({evt.time})"
            count = sum(
                1 for ac in self.app.acolytes
                if ac.id not in evt.excluded_acolyte_ids
            )
            entries.append({
                "date": d,
                "label": label,
                "type": "event",
                "unit": evt,
                "is_schedule": False,
                "count": count,
            })

        for ac in self.app.acolytes:
            if not ac.birthdate:
                continue
            d = _parse_date(ac.birthdate)
            if not d:
                continue
            # Normalize to current year for display
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

        # Sort newest first
        entries.sort(key=lambda e: e["date"], reverse=True)
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
                    if info.schedule_slots:
                        indicators.append("📋")
                    if info.general_events:
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

                hdr = ttk.Frame(self._tl_inner)
                hdr.pack(fill=tk.X, pady=(10, 2))

                if is_today:
                    lbl = tk.Label(
                        hdr, text=f"📌 {date_label} (Hoje)",
                        font=("TkDefaultFont", 11, "bold"),
                        bg="#4A90E2", fg="white",
                        padx=8, pady=2,
                    )
                else:
                    lbl = ttk.Label(
                        hdr, text=f"📅 {date_label}",
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
        DayDetailDialog(self, self.app, info)
        # Refresh after dialog closes
        self._draw_calendar()
        self._refresh_timeline()

    def _open_unit_detail(self, entry: dict):
        UnitDetailDialog(
            self, self.app,
            unit=entry["unit"],
            is_schedule=entry["is_schedule"],
            date_obj=entry["date"],
        )
        # Refresh after dialog closes
        self._draw_calendar()
        self._refresh_timeline()

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
