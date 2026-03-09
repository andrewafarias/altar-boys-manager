"""Widgets reutilizáveis: calendário, seletor de horário e campos compostos."""

import calendar
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from .base import BaseDialog


class CalendarDialog(BaseDialog):
    """Mini calendário para seleção de datas."""

    def __init__(self, parent, initial_date: str = "", date_format: str = "DD/MM/YYYY"):
        self._initial_date = initial_date
        self._date_format = date_format
        try:
            self._mouse_x = parent.winfo_pointerx()
            self._mouse_y = parent.winfo_pointery()
        except Exception:
            self._mouse_x = None
            self._mouse_y = None
        super().__init__(parent, "Selecionar Data")
        self._build()
        self._position_near_mouse()
        self.wait_window()

    def _position_near_mouse(self):
        self.update_idletasks()
        if self._mouse_x is not None and self._mouse_y is not None:
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = self._mouse_x - w // 2
            y = self._mouse_y - 10
            x = max(0, min(x, sw - w))
            y = max(0, min(y, sh - h))
            self.geometry(f"+{x}+{y}")
        else:
            self._center()

    def _build(self):
        self._cal_module = calendar

        today = datetime.now()
        self._view_year = today.year
        self._view_month = today.month

        if self._initial_date:
            try:
                parts = self._initial_date.strip().split("/")
                if len(parts) == 3:
                    self._view_year = int(parts[2])
                    self._view_month = int(parts[1])
                elif len(parts) == 2:
                    self._view_month = int(parts[1])
            except (ValueError, IndexError):
                pass

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        nav = ttk.Frame(frame)
        nav.pack(fill=tk.X, pady=4)
        ttk.Button(nav, text="◀", width=3, command=self._prev_month).pack(side=tk.LEFT)
        self._month_label = ttk.Label(
            nav, text="", width=20, anchor="center", font=("TkDefaultFont", 10, "bold")
        )
        self._month_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(nav, text="▶", width=3, command=self._next_month).pack(side=tk.RIGHT)

        self._cal_frame = ttk.Frame(frame)
        self._cal_frame.pack(pady=4)

        ttk.Button(frame, text="Cancelar", command=self._cancel).pack(pady=4)

        self._draw_calendar()

    def _draw_calendar(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        month_names = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        self._month_label.config(
            text=f"{month_names[self._view_month - 1]} {self._view_year}"
        )

        day_headers = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for col, name in enumerate(day_headers):
            ttk.Label(
                self._cal_frame, text=name, width=4, anchor="center",
                font=("TkDefaultFont", 8, "bold")
            ).grid(row=0, column=col, padx=1)

        today = datetime.now()
        today_day = today.day
        today_month = today.month
        today_year = today.year

        weeks = self._cal_module.monthcalendar(self._view_year, self._view_month)
        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self._cal_frame, text="", width=4).grid(
                        row=r + 1, column=c, padx=1, pady=1
                    )
                else:
                    is_today = (day == today_day and
                                self._view_month == today_month and
                                self._view_year == today_year)

                    if is_today:
                        btn = tk.Button(
                            self._cal_frame,
                            text=str(day),
                            width=4,
                            command=lambda d=day: self._select_day(d),
                            bg="#4A90E2",
                            fg="white",
                            font=("TkDefaultFont", 9, "bold"),
                            relief=tk.RAISED,
                            cursor="hand2"
                        )
                        btn.grid(row=r + 1, column=c, padx=1, pady=1)
                    else:
                        ttk.Button(
                            self._cal_frame,
                            text=str(day),
                            width=4,
                            command=lambda d=day: self._select_day(d),
                        ).grid(row=r + 1, column=c, padx=1, pady=1)

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

    def _select_day(self, day: int):
        if self._date_format == "DD/MM":
            self.result = f"{day:02d}/{self._view_month:02d}"
        else:
            self.result = f"{day:02d}/{self._view_month:02d}/{self._view_year}"
        self.destroy()

    def _ok(self):
        pass


class DateEntryFrame(ttk.Frame):
    """Frame composto com Entry de data e botão de calendário."""

    def __init__(self, parent, textvariable: tk.StringVar, width: int = 10,
                 date_format: str = "DD/MM/YYYY", **kwargs):
        super().__init__(parent, **kwargs)
        self._var = textvariable
        self._date_format = date_format
        ttk.Entry(self, textvariable=textvariable, width=width).pack(side=tk.LEFT)
        ttk.Button(self, text="📅", width=3, command=self._open_calendar).pack(
            side=tk.LEFT, padx=1
        )

    def _open_calendar(self):
        dlg = CalendarDialog(self, self._var.get(), self._date_format)
        if dlg.result:
            self._var.set(dlg.result)


class TimePickerDialog(BaseDialog):
    """Mini janela para seleção de horário com mouse."""

    _app = None  # Set by App.__init__ to allow persistent custom common times

    def __init__(self, parent, initial_time: str = ""):
        self._initial_time = initial_time
        try:
            self._mouse_x = parent.winfo_pointerx()
            self._mouse_y = parent.winfo_pointery()
        except Exception:
            self._mouse_x = None
            self._mouse_y = None
        super().__init__(parent, "Selecionar Horário")
        self._build()
        self._position_near_mouse()
        self.wait_window()

    def _position_near_mouse(self):
        self.update_idletasks()
        if self._mouse_x is not None and self._mouse_y is not None:
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = self._mouse_x - w // 2
            y = self._mouse_y - 10
            x = max(0, min(x, sw - w))
            y = max(0, min(y, sh - h))
            self.geometry(f"+{x}+{y}")
        else:
            self._center()

    def _get_common_times(self):
        if self._app is not None and hasattr(self._app, 'custom_common_times') and self._app.custom_common_times:
            return list(self._app.custom_common_times)
        from ..data_manager import DEFAULT_COMMON_TIMES
        return list(DEFAULT_COMMON_TIMES)

    def _build(self):
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecione o horário:", font=("TkDefaultFont", 10, "bold")).pack(
            pady=(0, 6)
        )

        init_h, init_m = 8, 0
        if self._initial_time:
            try:
                parts = self._initial_time.strip().split(":")
                init_h = int(parts[0])
                if len(parts) > 1:
                    init_m = int(parts[1])
            except (ValueError, IndexError):
                pass

        time_frame = ttk.Frame(frame)
        time_frame.pack(pady=4)

        ttk.Label(time_frame, text="Hora:").pack(side=tk.LEFT)
        self._hour_var = tk.StringVar(value=str(init_h))
        hour_spin = ttk.Spinbox(
            time_frame, from_=0, to=23, textvariable=self._hour_var,
            width=4, wrap=True, format="%02.0f"
        )
        hour_spin.pack(side=tk.LEFT, padx=2)

        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)

        self._min_var = tk.StringVar(value=f"{init_m:02d}")
        min_spin = ttk.Spinbox(
            time_frame, from_=0, to=59, textvariable=self._min_var,
            width=4, wrap=True, format="%02.0f", increment=5
        )
        min_spin.pack(side=tk.LEFT, padx=2)

        # Common times section
        common_label_frame = ttk.Frame(frame)
        common_label_frame.pack(fill=tk.X, pady=(8, 2))
        ttk.Label(common_label_frame, text="Horários comuns:", foreground="gray").pack(side=tk.LEFT)

        # Scrollable list of common times
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.X)
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._times_listbox = tk.Listbox(
            list_frame, yscrollcommand=sb.set, height=5, selectmode=tk.SINGLE, exportselection=False
        )
        self._times_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sb.config(command=self._times_listbox.yview)
        self._times_listbox.bind("<Double-Button-1>", lambda e: self._select_from_list())
        self._populate_times_listbox()

        # Add / Remove row
        manage_frame = ttk.Frame(frame)
        manage_frame.pack(fill=tk.X, pady=4)
        self._new_time_var = tk.StringVar()
        ttk.Entry(manage_frame, textvariable=self._new_time_var, width=7).pack(side=tk.LEFT, padx=2)
        ttk.Button(manage_frame, text="➕", width=3, command=self._add_common_time).pack(side=tk.LEFT, padx=1)
        ttk.Button(manage_frame, text="🗑️", width=3, command=self._remove_common_time).pack(side=tk.LEFT, padx=1)
        ttk.Button(manage_frame, text="Usar Selecionado", command=self._select_from_list).pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _populate_times_listbox(self):
        self._times_listbox.delete(0, tk.END)
        for t in self._get_common_times():
            self._times_listbox.insert(tk.END, t)

    def _select_from_list(self):
        sel = self._times_listbox.curselection()
        if sel:
            time_str = self._times_listbox.get(sel[0])
            self.result = time_str
            self.destroy()

    def _add_common_time(self):
        time_str = self._new_time_var.get().strip()
        if not time_str:
            return
        # Validate HH:MM format
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            time_str = f"{h:02d}:{m:02d}"
        except ValueError:
            from tkinter import messagebox as mb
            mb.showwarning("Aviso", "Informe um horário válido no formato HH:MM.", parent=self)
            return
        times = self._get_common_times()
        if time_str not in times:
            times.append(time_str)
            times.sort()
            if self._app is not None:
                self._app.custom_common_times = times
                self._app.save()
        self._new_time_var.set("")
        self._populate_times_listbox()

    def _remove_common_time(self):
        sel = self._times_listbox.curselection()
        if not sel:
            return
        time_str = self._times_listbox.get(sel[0])
        times = self._get_common_times()
        if time_str in times:
            times.remove(time_str)
            if self._app is not None:
                self._app.custom_common_times = times
                self._app.save()
        self._populate_times_listbox()

    def _ok(self):
        try:
            h = int(self._hour_var.get())
            m = int(self._min_var.get())
            self.result = f"{h:02d}:{m:02d}"
        except (ValueError, tk.TclError):
            self.result = self._hour_var.get() + ":" + self._min_var.get()
        self.destroy()


class TimeEntryFrame(ttk.Frame):
    """Frame composto com Entry de hora e botão de relógio."""

    def __init__(self, parent, textvariable: tk.StringVar, width: int = 6, **kwargs):
        super().__init__(parent, **kwargs)
        self._var = textvariable
        ttk.Entry(self, textvariable=textvariable, width=width).pack(side=tk.LEFT)
        ttk.Button(self, text="🕐", width=3, command=self._open_time_picker).pack(
            side=tk.LEFT, padx=1
        )

    def _open_time_picker(self):
        dlg = TimePickerDialog(self, self._var.get())
        if dlg.result:
            self._var.set(dlg.result)
