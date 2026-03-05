"""Aplicação principal de gerenciamento de escala de acólitos."""

import sys
import uuid
import calendar
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, timedelta
from typing import List, Optional

import data_manager
import report_generator
from models import (
    Acolyte,
    Absence,
    Suspension,
    BonusMovement,
    ScheduleHistoryEntry,
    EventHistoryEntry,
    ScheduleSlot,
    GeneralEvent,
    GeneratedScheduleSlotSnapshot,
    GeneratedSchedule,
    FinalizedEventBatch,
    FinalizedEventBatchEntry,
    StandardSlot,
)

# Nomes dos dias da semana em português
WEEKDAYS_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]


def detect_weekday(date_str: str) -> str:
    """Detecta o dia da semana a partir de uma data no formato DD/MM ou DD/MM/YYYY."""
    try:
        parts = date_str.strip().split("/")
        if len(parts) >= 2:
            day, month = int(parts[0]), int(parts[1])
            year = int(parts[2]) if len(parts) == 3 else datetime.now().year
            dt = datetime(year, month, day)
            return WEEKDAYS_PT[dt.weekday()]
    except (ValueError, IndexError):
        pass
    return ""


def today_str() -> str:
    """Retorna a data de hoje no formato DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")


def next_occurrence_of_day(day_name: str) -> str:
    """Retorna a data (DD/MM) da próxima ocorrência do dia da semana indicado."""
    try:
        target_idx = WEEKDAYS_PT.index(day_name)
    except ValueError:
        return ""
    today = datetime.now()
    current_idx = today.weekday()
    days_ahead = target_idx - current_idx
    if days_ahead <= 0:
        days_ahead += 7
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%d/%m")


def names_list_to_text(names: List[str]) -> str:
    """Formata uma lista de nomes separando o último com 'e'."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " e " + names[-1]


# ---------------------------------------------------------------------------
# Diálogos
# ---------------------------------------------------------------------------

class BaseDialog(tk.Toplevel):
    """Base para diálogos modais."""

    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
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

    def _ok(self):
        raise NotImplementedError

    def _cancel(self):
        self.result = None
        self.destroy()


class AddAbsenceDialog(BaseDialog):
    """Diálogo para registrar uma falta."""

    def __init__(self, parent):
        super().__init__(parent, "Registrar Falta")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.date_var, width=14, date_format="DD/MM/YYYY").grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(row=1, column=1, padx=8, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        date = self.date_var.get().strip()
        desc = self.desc_var.get().strip()
        if not date:
            messagebox.showwarning("Aviso", "Informe a data.", parent=self)
            return
        self.result = (date, desc)
        self.destroy()


class SuspendDialog(BaseDialog):
    """Diálogo para suspender um acólito."""

    def __init__(self, parent):
        super().__init__(parent, "Suspender Acólito")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Motivo:").grid(row=0, column=0, sticky="w", pady=4)
        self.reason_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.reason_var, width=30).grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Data de início (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.start_var, width=14, date_format="DD/MM/YYYY").grid(row=1, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Data de fim (DD/MM/YYYY):").grid(row=2, column=0, sticky="w", pady=4)
        self.end_var = tk.StringVar()
        DateEntryFrame(frame, textvariable=self.end_var, width=14, date_format="DD/MM/YYYY").grid(row=2, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Duração:").grid(row=3, column=0, sticky="w", pady=4)
        self.duration_var = tk.StringVar()
        e = ttk.Entry(frame, textvariable=self.duration_var, width=20)
        e.grid(row=3, column=1, padx=8, pady=4)
        e.insert(0, "ex: 2 semanas")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        reason = self.reason_var.get().strip()
        start = self.start_var.get().strip()
        duration = self.duration_var.get().strip()
        end_date = self.end_var.get().strip()
        if not reason:
            messagebox.showwarning("Aviso", "Informe o motivo.", parent=self)
            return
        self.result = (reason, start, duration, end_date)
        self.destroy()


class SelectSuspensionsDialog(BaseDialog):
    """Diálogo para selecionar quais suspensões ativas desativar."""

    def __init__(self, parent, suspensions: list):
        self._suspensions = suspensions
        super().__init__(parent, "Selecionar Suspensões para Levantar")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecione as suspensões que deseja levantar:").pack(anchor="w", pady=(0, 6))

        self._vars = []
        for susp in self._suspensions:
            var = tk.BooleanVar(value=True)
            self._vars.append((susp, var))
            end_info = f" (até {susp.end_date})" if susp.end_date else ""
            text = f"{susp.reason} - Início: {susp.start_date}{end_info}"
            ttk.Checkbutton(frame, text=text, variable=var).pack(anchor="w", padx=4, pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        selected = [susp for susp, var in self._vars if var.get()]
        if not selected:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma suspensão.", parent=self)
            return
        self.result = selected
        self.destroy()


class EditSuspensionDialog(BaseDialog):
    """Diálogo para editar uma suspensão."""

    def __init__(self, parent, suspension):
        self._suspension = suspension
        super().__init__(parent, "Editar Suspensão")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Motivo:").grid(row=0, column=0, sticky="w", pady=4)
        self.reason_var = tk.StringVar(value=self._suspension.reason)
        ttk.Entry(frame, textvariable=self.reason_var, width=30).grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Data de início:").grid(row=1, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar(value=self._suspension.start_date)
        DateEntryFrame(frame, textvariable=self.start_var, width=14, date_format="DD/MM/YYYY").grid(row=1, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Data de fim:").grid(row=2, column=0, sticky="w", pady=4)
        self.end_var = tk.StringVar(value=self._suspension.end_date)
        DateEntryFrame(frame, textvariable=self.end_var, width=14, date_format="DD/MM/YYYY").grid(row=2, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Duração:").grid(row=3, column=0, sticky="w", pady=4)
        self.duration_var = tk.StringVar(value=self._suspension.duration)
        ttk.Entry(frame, textvariable=self.duration_var, width=20).grid(row=3, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Ativa:").grid(row=4, column=0, sticky="w", pady=4)
        self.active_var = tk.BooleanVar(value=self._suspension.is_active)
        ttk.Checkbutton(frame, variable=self.active_var).grid(row=4, column=1, padx=8, pady=4, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        self.result = {
            "reason": self.reason_var.get().strip(),
            "start_date": self.start_var.get().strip(),
            "end_date": self.end_var.get().strip(),
            "duration": self.duration_var.get().strip(),
            "is_active": self.active_var.get(),
        }
        self.destroy()


class BonusDialog(BaseDialog):
    """Diálogo para dar ou usar bônus."""

    def __init__(self, parent, bonus_type: str):
        self.bonus_type = bonus_type
        title = "Dar Bônus" if bonus_type == "earn" else "Usar Bônus"
        super().__init__(parent, title)
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Quantidade:").grid(row=0, column=0, sticky="w", pady=4)
        self.amount_var = tk.StringVar(value="1")
        ttk.Spinbox(frame, from_=1, to=99, textvariable=self.amount_var, width=8).grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(row=1, column=1, padx=8, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        try:
            amount = int(self.amount_var.get().strip())
            if amount < 1:
                amount = 1
        except (ValueError, tk.TclError):
            amount = 1
        desc = self.desc_var.get().strip()
        self.result = (amount, desc)
        self.destroy()


class FinalizeScheduleDialog(BaseDialog):
    """Diálogo que exibe o texto gerado da escala."""

    def __init__(self, parent, text: str):
        super().__init__(parent, "Escala Gerada")
        self._text = text
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Texto da escala:").pack(anchor="w")

        txt_frame = ttk.Frame(frame)
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        scrollbar = ttk.Scrollbar(txt_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            txt_frame,
            width=60,
            height=20,
            yscrollcommand=scrollbar.set,
            state=tk.NORMAL,
            font=("Courier", 10),
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        self.text_widget.insert(tk.END, self._text)
        self.text_widget.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=8)
        ttk.Button(
            btn_frame, text="📋 Copiar para Área de Transferência", command=self._copy
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Fechar", command=self.destroy).pack(side=tk.LEFT, padx=4)

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self._text)
        messagebox.showinfo("Copiado", "Texto copiado para a área de transferência!", parent=self)


class AddEventDialog(BaseDialog):
    """Diálogo para adicionar um evento geral."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Evento")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nome do evento:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Data (DD/MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar()
        DateEntryFrame(frame, textvariable=self.date_var, width=8, date_format="DD/MM").grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Horário (opcional, HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(row=2, column=1, padx=8, pady=4, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        name = self.name_var.get().strip()
        date = self.date_var.get().strip()
        time = self.time_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Informe o nome do evento.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data do evento.", parent=self)
            return
        self.result = (name, date, time)
        self.destroy()


class AddMultipleAcolytesDialog(BaseDialog):
    """Diálogo para adicionar múltiplos acólitos de uma vez."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Acólitos")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame, 
            text="Digite os nomes dos acólitos (um por linha):"
        ).pack(anchor="w", pady=(0, 4))

        # Text widget for multiple names
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            text_frame,
            width=40,
            height=10,
            yscrollcommand=scrollbar.set,
            font=("TkDefaultFont", 10),
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        self.text_widget.focus()

        ttk.Label(
            frame,
            text="💡 Dica: Também pode separar por vírgula",
            foreground="gray"
        ).pack(anchor="w", pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Adicionar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        text = self.text_widget.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Aviso", "Informe pelo menos um nome.", parent=self)
            return
        
        # Parse names - support both newlines and commas
        names = []
        for line in text.split('\n'):
            # Split by comma if present
            if ',' in line:
                names.extend([n.strip() for n in line.split(',') if n.strip()])
            else:
                if line.strip():
                    names.append(line.strip())
        
        if not names:
            messagebox.showwarning("Aviso", "Informe pelo menos um nome válido.", parent=self)
            return
        
        self.result = names
        self.destroy()


class CalendarDialog(BaseDialog):
    """Mini calendário para seleção de datas."""

    def __init__(self, parent, initial_date: str = "", date_format: str = "DD/MM/YYYY"):
        self._initial_date = initial_date
        self._date_format = date_format  # "DD/MM/YYYY" or "DD/MM"
        # Capture mouse position before dialog is built
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
        """Position the dialog near the mouse cursor."""
        self.update_idletasks()
        if self._mouse_x is not None and self._mouse_y is not None:
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = self._mouse_x - w // 2
            y = self._mouse_y - 10
            # Keep within screen bounds
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

        weeks = self._cal_module.monthcalendar(self._view_year, self._view_month)
        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self._cal_frame, text="", width=4).grid(
                        row=r + 1, column=c, padx=1, pady=1
                    )
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
        """Position the dialog near the mouse cursor."""
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
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecione o horário:", font=("TkDefaultFont", 10, "bold")).pack(
            pady=(0, 6)
        )

        # Parse initial time
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

        # Quick hour buttons
        ttk.Label(frame, text="Horários comuns:", foreground="gray").pack(anchor="w", pady=(6, 2))
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill=tk.X)
        common_times = [
            "06:00", "07:00", "08:00", "09:00", "10:00",
            "11:00", "12:00", "14:00", "15:00", "16:00",
            "17:00", "18:00", "19:00", "19:30", "20:00",
        ]
        for i, t in enumerate(common_times):
            ttk.Button(
                quick_frame, text=t, width=5,
                command=lambda t=t: self._select_quick(t),
            ).grid(row=i // 5, column=i % 5, padx=1, pady=1)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _select_quick(self, time_str: str):
        self.result = time_str
        self.destroy()

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


# ---------------------------------------------------------------------------
# Painel de slot de escala (widget reutilizável)
# ---------------------------------------------------------------------------

class ScheduleSlotCard(ttk.LabelFrame):
    """
    Widget que representa um horário de escala.
    Exibe campos de data, horário, descrição e lista de acólitos atribuídos.
    """

    def __init__(self, parent, slot: ScheduleSlot, app, **kwargs):
        title = f"⛪ Evento Geral #{slot.id[:6]}" if slot.is_general_event else f"Horário #{slot.id[:6]}"
        super().__init__(parent, text=title, padding=6, **kwargs)
        self.slot = slot
        self.app = app
        self._acolyte_labels: dict = {}
        self._build()
        self._refresh_acolytes()

    def _build(self):
        # Linha 1: data, horário, descrição, remover
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Data:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=self.slot.date)
        self.date_var.trace_add("write", self._on_date_change)
        DateEntryFrame(row1, textvariable=self.date_var, width=6, date_format="DD/MM").pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Hora:").pack(side=tk.LEFT, padx=(6, 0))
        self.time_var = tk.StringVar(value=self.slot.time)
        self.time_var.trace_add("write", self._on_field_change)
        TimeEntryFrame(row1, textvariable=self.time_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Descrição:").pack(side=tk.LEFT, padx=(6, 0))
        self.desc_var = tk.StringVar(value=self.slot.description)
        self.desc_var.trace_add("write", self._on_field_change)
        ttk.Entry(row1, textvariable=self.desc_var, width=20).pack(side=tk.LEFT, padx=2)

        ttk.Button(row1, text="✕", width=3, command=self._remove_self).pack(side=tk.RIGHT, padx=2)

        # Linha 2: dia da semana
        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Dia:").pack(side=tk.LEFT)
        self.day_var = tk.StringVar(value=self.slot.day)
        self.day_combo = ttk.Combobox(
            row2, textvariable=self.day_var, values=WEEKDAYS_PT, width=16, state="readonly"
        )
        self.day_combo.pack(side=tk.LEFT, padx=2)
        self.day_var.trace_add("write", self._on_field_change)

        # Linha 3: acólitos atribuídos
        self.acolyte_frame = ttk.Frame(self)
        self.acolyte_frame.pack(fill=tk.X, pady=2)

        # Linha 4: botão adicionar acólito selecionado
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
        if detected:
            self.day_var.set(detected)
        self._on_field_change()

    def _on_field_change(self, *_):
        self.slot.date = self.date_var.get().strip()
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
            messagebox.showinfo("Aviso", "Selecione um ou mais acólitos na lista à direita.", parent=self)
            return
        added = []
        for acolyte in acolytes:
            if acolyte.id not in self.slot.acolyte_ids:
                self.slot.acolyte_ids.append(acolyte.id)
                added.append(acolyte.name)
        if added:
            self._refresh_acolytes()
            self.app.save()
        else:
            messagebox.showinfo("Aviso", "Acólito(s) selecionado(s) já estão neste horário.", parent=self)

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
            ttk.Label(self.acolyte_frame, text="(nenhum acólito)", foreground="gray").pack(side=tk.LEFT)
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
        """Atualiza a exibição de acólitos (chame quando nomes mudarem)."""
        self._refresh_acolytes()


# ---------------------------------------------------------------------------
# Diálogo de horários padrão
# ---------------------------------------------------------------------------

class StandardSlotsDialog(BaseDialog):
    """Diálogo para gerenciar horários padrão."""

    def __init__(self, parent, app):
        self.app = app
        super().__init__(parent, "Gerenciar Horários Padrão")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Horários padrão são adicionados automaticamente à escala.",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 6))

        # List
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=sb.set, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.listbox.yview)

        self._refresh_list()

        # Add form
        add_frame = ttk.LabelFrame(frame, text="Adicionar Horário Padrão", padding=8)
        add_frame.pack(fill=tk.X, pady=6)

        ttk.Label(add_frame, text="Dia:").grid(row=0, column=0, sticky="w", pady=2)
        self._day_var = tk.StringVar()
        ttk.Combobox(
            add_frame, textvariable=self._day_var, values=WEEKDAYS_PT, width=16, state="readonly"
        ).grid(row=0, column=1, padx=4, pady=2, sticky="w")

        ttk.Label(add_frame, text="Hora:").grid(row=1, column=0, sticky="w", pady=2)
        self._time_var = tk.StringVar()
        TimeEntryFrame(add_frame, textvariable=self._time_var, width=8).grid(
            row=1, column=1, padx=4, pady=2, sticky="w"
        )

        ttk.Label(add_frame, text="Descrição:").grid(row=2, column=0, sticky="w", pady=2)
        self._desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._desc_var, width=24).grid(
            row=2, column=1, padx=4, pady=2, sticky="w"
        )

        ttk.Button(add_frame, text="➕ Adicionar", command=self._add_slot).grid(
            row=3, column=0, columnspan=2, pady=6
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="🗑️ Remover Selecionado", command=self._remove_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="📋 Adicionar à Escala Atual", command=self._add_to_schedule).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_row, text="Fechar", command=self.destroy).pack(side=tk.RIGHT, padx=4)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for ss in self.app.standard_slots:
            self.listbox.insert(tk.END, f"{ss.day} {ss.time} - {ss.description}")

    def _add_slot(self):
        day = self._day_var.get().strip()
        time = self._time_var.get().strip()
        desc = self._desc_var.get().strip()
        if not day:
            messagebox.showwarning("Aviso", "Selecione o dia da semana.", parent=self)
            return
        ss = StandardSlot(id=str(uuid.uuid4()), day=day, time=time, description=desc)
        self.app.standard_slots.append(ss)
        self.app.save()
        self._refresh_list()

    def _remove_slot(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um horário padrão.", parent=self)
            return
        idx = sel[0]
        if idx < len(self.app.standard_slots):
            self.app.standard_slots.pop(idx)
            self.app.save()
            self._refresh_list()

    def _add_to_schedule(self):
        if not self.app.standard_slots:
            messagebox.showinfo("Aviso", "Nenhum horário padrão cadastrado.", parent=self)
            return
        for ss in self.app.standard_slots:
            auto_date = next_occurrence_of_day(ss.day)
            slot = ScheduleSlot(id=str(uuid.uuid4()), date=auto_date, day=ss.day, time=ss.time, description=ss.description)
            self.app.schedule_slots.append(slot)
        self.app.schedule_tab.load_slots_from_data()
        self.app.save()
        messagebox.showinfo(
            "Concluído",
            f"{len(self.app.standard_slots)} horário(s) padrão adicionado(s) à escala.\nDatas preenchidas automaticamente.",
            parent=self,
        )

    def _ok(self):
        pass


# ---------------------------------------------------------------------------
# Aba 1: Criar Escala
# ---------------------------------------------------------------------------

class ScheduleTab(ttk.Frame):
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
        paned.add(left, minsize=500)

        header = ttk.Frame(left)
        header.pack(fill=tk.X, pady=4)
        ttk.Label(header, text="Criar Nova Escala", font=("TkDefaultFont", 12, "bold")).pack(side=tk.LEFT)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row, text="➕ Adicionar Horário", command=self._add_slot).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="⛪ Evento Geral", command=self._add_general_event_slot).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="📋 Horários Padrão", command=self._manage_standard_slots).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="🗑️ Limpar Escala", command=self._clear_schedule).pack(side=tk.LEFT, padx=4)

        # Área rolável para os cards
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

        # Botão finalizar
        ttk.Button(
            left,
            text="✅ Finalizar Escala",
            command=self._finalize_schedule,
            style="Accent.TButton",
        ).pack(fill=tk.X, pady=8, padx=4)

        # --- Painel direito ---
        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=220)

        ttk.Label(right, text="Acólitos", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        # Sorting/filtering controls
        ctrl_frame = ttk.Frame(right)
        ctrl_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ctrl_frame, text="Ordem:").pack(side=tk.LEFT)
        self._sort_dir_var = tk.StringVar(value="asc")
        ttk.Radiobutton(ctrl_frame, text="↑ Crescente", variable=self._sort_dir_var,
                        value="asc", command=self.refresh_acolyte_list).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(ctrl_frame, text="↓ Decrescente", variable=self._sort_dir_var,
                        value="desc", command=self.refresh_acolyte_list).pack(side=tk.LEFT, padx=2)

        self._include_events_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right, text="Incluir eventos no total",
            variable=self._include_events_var,
            command=self.refresh_acolyte_list,
        ).pack(anchor="w", padx=4)

        ttk.Label(right, text="(Ctrl+clique para múltiplos)", foreground="gray",
                  font=("TkDefaultFont", 8)).pack(anchor="w", padx=4)

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
        """Retorna o primeiro acólito selecionado na lista."""
        acolytes = self.get_selected_acolytes()
        return acolytes[0] if acolytes else None

    def get_selected_acolytes(self) -> List[Acolyte]:
        """Retorna todos os acólitos selecionados na lista."""
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
        """Add a slot linked to a general event."""
        dlg = AddEventDialog(self.app.root)
        if dlg.result:
            name, date, time = dlg.result
            slot = ScheduleSlot(
                id=str(uuid.uuid4()),
                date=date,
                day=detect_weekday(date),
                time=time,
                description=name,
                is_general_event=True,
                general_event_name=name,
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
        """Abre o diálogo de gerenciamento de horários padrão."""
        dlg = StandardSlotsDialog(self.app.root, self.app)
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

        # Build history snapshot
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

        # Atualiza contadores e histórico de cada acólito
        for slot in self.app.schedule_slots:
            if not slot.is_general_event:
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

        # Register general events
        for slot in general_event_slots:
            ev = GeneralEvent(
                id=str(uuid.uuid4()),
                name=slot.general_event_name or slot.description,
                date=slot.date,
                time=slot.time,
            )
            self.app.general_events.append(ev)

        # Limpa os slots após finalizar
        self.app.schedule_slots.clear()
        self._slot_cards.clear()
        for widget in self.slots_frame.winfo_children():
            widget.destroy()

        self.app.save()
        self.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()
        self.app.events_tab.refresh_list()

        # Refresh history tab
        if hasattr(self.app, 'history_tab'):
            self.app.history_tab.refresh()

        # Exibe o diálogo com o texto gerado
        FinalizeScheduleDialog(self.app.root, text)


# ---------------------------------------------------------------------------
# Aba 2: Eventos Gerais
# ---------------------------------------------------------------------------

class EventsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._current_event: Optional[GeneralEvent] = None
        self._acolyte_vars: dict = {}
        self._build()

    def _build(self):
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Painel esquerdo: lista de eventos ---
        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=240)

        ttk.Button(left, text="➕ Adicionar Evento", command=self._add_event).pack(fill=tk.X, pady=4)

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

        ttk.Button(left, text="🗑️ Remover Evento", command=self._remove_event).pack(fill=tk.X, pady=4)

        # Botão registrar eventos
        ttk.Button(
            left,
            text="✅ Registrar Eventos",
            command=self._finalize_events,
        ).pack(fill=tk.X, pady=4)

        # --- Painel direito: detalhes do evento ---
        self.right = ttk.Frame(paned, padding=4)
        paned.add(self.right, minsize=400)
        self._build_event_detail()

    def _build_event_detail(self):
        """Constrói o painel de detalhes (inicialmente vazio)."""
        self.detail_label = ttk.Label(
            self.right, text="Selecione um evento para editar.", foreground="gray"
        )
        self.detail_label.pack(pady=20)

        self.detail_frame = ttk.Frame(self.right)

        # Campos editáveis
        fields = ttk.Frame(self.detail_frame)
        fields.pack(fill=tk.X)

        ttk.Label(fields, text="Nome:").grid(row=0, column=0, sticky="w", pady=4)
        self.ev_name_var = tk.StringVar()
        ttk.Entry(fields, textvariable=self.ev_name_var, width=28).grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(fields, text="Data (DD/MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.ev_date_var = tk.StringVar()
        DateEntryFrame(fields, textvariable=self.ev_date_var, width=8, date_format="DD/MM").grid(row=1, column=1, padx=6, pady=4, sticky="w")

        ttk.Label(fields, text="Horário:").grid(row=2, column=0, sticky="w", pady=4)
        self.ev_time_var = tk.StringVar()
        TimeEntryFrame(fields, textvariable=self.ev_time_var, width=10).grid(row=2, column=1, padx=6, pady=4, sticky="w")

        # Participantes
        ttk.Label(self.detail_frame, text="Participantes:", font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w", pady=(8, 2)
        )

        part_scroll_frame = ttk.Frame(self.detail_frame)
        part_scroll_frame.pack(fill=tk.BOTH, expand=True)

        part_canvas = tk.Canvas(part_scroll_frame, height=200, highlightthickness=0)
        part_vscroll = ttk.Scrollbar(part_scroll_frame, orient=tk.VERTICAL, command=part_canvas.yview)
        part_canvas.configure(yscrollcommand=part_vscroll.set)
        part_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        part_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.participants_inner = ttk.Frame(part_canvas)
        self.participants_window = part_canvas.create_window((0, 0), window=self.participants_inner, anchor="nw")

        def on_configure(event):
            part_canvas.configure(scrollregion=part_canvas.bbox("all"))

        self.participants_inner.bind("<Configure>", on_configure)

        ttk.Button(self.detail_frame, text="💾 Salvar Evento", command=self._save_event).pack(
            fill=tk.X, pady=8
        )

    def _show_detail(self):
        self.detail_label.pack_forget()
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    def _hide_detail(self):
        self.detail_frame.pack_forget()
        self.detail_label.pack(pady=20)

    def refresh_list(self):
        """Atualiza a listbox de eventos."""
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
        self.ev_name_var.set(ev.name)
        self.ev_date_var.set(ev.date)
        self.ev_time_var.set(ev.time)
        self._rebuild_participants()

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
            self._acolyte_vars[ac.id] = var
            ttk.Checkbutton(
                self.participants_inner, text=ac.name, variable=var
            ).pack(anchor="w", padx=4)

    def _save_event(self):
        if not self._current_event:
            return
        ev = self._current_event
        ev.name = self.ev_name_var.get().strip()
        ev.date = self.ev_date_var.get().strip()
        ev.time = self.ev_time_var.get().strip()

        ev.excluded_acolyte_ids = [
            aid for aid, var in self._acolyte_vars.items() if not var.get()
        ]
        self.refresh_list()
        self.app.save()
        messagebox.showinfo("Salvo", "Evento salvo com sucesso!")

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
            messagebox.showinfo("Aviso", "Selecione um evento para remover.")
            return
        idx = sel[0]
        if idx >= len(self.app.general_events):
            return
        ev = self.app.general_events[idx]
        if not messagebox.askyesno("Confirmar", f"Remover evento '{ev.name}'?"):
            return
        self.app.general_events.pop(idx)
        self._current_event = None
        self._hide_detail()
        self.refresh_list()
        self.app.save()

    def _finalize_events(self):
        if not self.app.general_events:
            messagebox.showinfo("Aviso", "Nenhum evento cadastrado.")
            return
        if not messagebox.askyesno(
            "Confirmar",
            "Deseja registrar todos os eventos? Os eventos serão contabilizados e removidos da aba.",
        ):
            return
        batch_id = str(uuid.uuid4())
        entries = []
        count = 0
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
        # Clear events after registering
        self.app.general_events.clear()
        self._current_event = None
        self._hide_detail()
        self.refresh_list()
        self.app.save()
        if hasattr(self.app, 'history_tab'):
            self.app.history_tab.refresh()
        messagebox.showinfo("Concluído", f"Eventos registrados! {count} registros adicionados.")


# ---------------------------------------------------------------------------
# Aba 3: Acólitos
# ---------------------------------------------------------------------------

class AcolytesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._current_acolyte: Optional[Acolyte] = None
        self._build()

    def _build(self):
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Painel esquerdo ---
        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=200)

        ttk.Button(left, text="➕ Adicionar Acólito", command=self._add_acolyte).pack(fill=tk.X, pady=4)
        ttk.Button(left, text="🗑️ Remover Acólito", command=self._remove_acolyte).pack(fill=tk.X, pady=2)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=4)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.acolyte_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("TkDefaultFont", 9),
        )
        self.acolyte_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.acolyte_listbox.yview)
        self.acolyte_listbox.bind("<<ListboxSelect>>", self._on_acolyte_select)

        # Botões do rodapé
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
        ttk.Button(left, text="📊 Visão Geral", command=self._show_overview_table).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="📕 Fechar Semestre", command=self._close_semester).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="📄 Gerar Relatório PDF", command=self._generate_report).pack(fill=tk.X, pady=2)

        # --- Painel direito ---
        self.right = ttk.Frame(paned, padding=6)
        paned.add(self.right, minsize=480)
        self._build_detail_panel()

    def _build_detail_panel(self):
        """Constrói o painel de detalhes do acólito."""
        self.no_selection_label = ttk.Label(
            self.right, text="Selecione um acólito para ver os detalhes.", foreground="gray"
        )
        self.no_selection_label.pack(pady=20)

        self.detail_frame = ttk.Frame(self.right)

        # Cabeçalho: nome e resumo
        self.name_label = ttk.Label(self.detail_frame, text="", font=("TkDefaultFont", 14, "bold"))
        self.name_label.pack(anchor="w")
        self.summary_label = ttk.Label(self.detail_frame, text="", foreground="#555")
        self.summary_label.pack(anchor="w", pady=2)

        # Seção de ações
        actions = ttk.Frame(self.detail_frame)
        actions.pack(fill=tk.X, pady=6)

        # Suspensão
        susp_frame = ttk.LabelFrame(actions, text="Suspensão", padding=4)
        susp_frame.pack(side=tk.LEFT, padx=4)
        ttk.Button(susp_frame, text="Suspender", command=self._suspend).pack(side=tk.LEFT, padx=2)
        ttk.Button(susp_frame, text="Levantar Suspensão", command=self._lift_suspension).pack(side=tk.LEFT, padx=2)

        # Faltas
        abs_frame = ttk.LabelFrame(actions, text="Faltas", padding=4)
        abs_frame.pack(side=tk.LEFT, padx=4)
        ttk.Button(abs_frame, text="Registrar Falta", command=self._add_absence).pack()

        # Bônus
        bonus_frame = ttk.LabelFrame(actions, text="Bônus", padding=4)
        bonus_frame.pack(side=tk.LEFT, padx=4)
        ttk.Button(bonus_frame, text="Dar Bônus", command=self._give_bonus).pack(side=tk.LEFT, padx=2)
        ttk.Button(bonus_frame, text="Usar Bônus", command=self._use_bonus).pack(side=tk.LEFT, padx=2)
        ttk.Label(bonus_frame, text="Qtd:").pack(side=tk.LEFT, padx=(6, 0))
        self.bonus_direct_var = tk.StringVar(value="0")
        self.bonus_spin = ttk.Spinbox(
            bonus_frame,
            from_=0,
            to=9999,
            textvariable=self.bonus_direct_var,
            width=6,
            command=self._set_bonus_direct,
        )
        self.bonus_spin.pack(side=tk.LEFT, padx=2)
        self.bonus_spin.bind("<Return>", lambda e: self._set_bonus_direct())
        self.bonus_spin.bind("<FocusOut>", lambda e: self._set_bonus_direct())

        # Notebook de detalhes
        self.detail_notebook = ttk.Notebook(self.detail_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True, pady=6)

        self._tab_schedule = ttk.Frame(self.detail_notebook)
        self._tab_events = ttk.Frame(self.detail_notebook)
        self._tab_absences = ttk.Frame(self.detail_notebook)
        self._tab_suspensions = ttk.Frame(self.detail_notebook)
        self._tab_bonus = ttk.Frame(self.detail_notebook)

        self.detail_notebook.add(self._tab_schedule, text="Histórico de Escalas")
        self.detail_notebook.add(self._tab_events, text="Eventos")
        self.detail_notebook.add(self._tab_absences, text="Faltas")
        self.detail_notebook.add(self._tab_suspensions, text="Suspensões")
        self.detail_notebook.add(self._tab_bonus, text="Movimentação de Bônus")

        # Criação das tabelas
        self._tree_schedule = self._make_tree(
            self._tab_schedule, ("Data", "Dia", "Horário", "Descrição"), (80, 120, 70, 200)
        )
        # Add edit/delete buttons for schedule history
        sched_btn_frame = ttk.Frame(self._tab_schedule)
        sched_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(sched_btn_frame, text="🗑️ Excluir Entrada", command=self._delete_schedule_entry).pack(side=tk.LEFT, padx=2)

        self._tree_events = self._make_tree(
            self._tab_events, ("Nome do Evento", "Data", "Horário"), (220, 80, 80)
        )
        # Add edit/delete buttons for event history
        event_btn_frame = ttk.Frame(self._tab_events)
        event_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(event_btn_frame, text="🗑️ Excluir Entrada", command=self._delete_event_entry).pack(side=tk.LEFT, padx=2)

        self._tree_absences = self._make_tree(
            self._tab_absences, ("Data", "Descrição"), (100, 300)
        )
        self._tree_suspensions = self._make_tree(
            self._tab_suspensions, ("Motivo", "Início", "Fim", "Duração", "Ativa"), (160, 90, 90, 80, 60)
        )
        # Add edit/delete buttons for suspensions
        susp_btn_frame = ttk.Frame(self._tab_suspensions)
        susp_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(susp_btn_frame, text="✏️ Editar Suspensão", command=self._edit_suspension).pack(side=tk.LEFT, padx=2)
        ttk.Button(susp_btn_frame, text="🗑️ Excluir Suspensão", command=self._delete_suspension).pack(side=tk.LEFT, padx=2)

        self._tree_bonus = self._make_tree(
            self._tab_bonus, ("Tipo", "Quantidade", "Descrição", "Data"), (70, 80, 220, 90)
        )

    def _make_tree(self, parent, columns, widths) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(
            frame, columns=columns, show="headings", yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, minwidth=50)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def refresh_list(self):
        """Atualiza a listbox com acólitos em ordem alfabética."""
        sel_id = None
        sel = self.acolyte_listbox.curselection()
        sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
        if sel:
            idx = sel[0]
            if idx < len(sorted_acs):
                sel_id = sorted_acs[idx].id

        self.acolyte_listbox.delete(0, tk.END)
        for ac in sorted_acs:
            suffix = " ⚠ suspenso" if ac.is_suspended else ""
            self.acolyte_listbox.insert(tk.END, f"{ac.name}{suffix}")

        for i, ac in enumerate(sorted_acs):
            if ac.is_suspended:
                # Check for expired suspension end_date
                has_expired = False
                for s in ac.suspensions:
                    if s.is_active and s.end_date:
                        try:
                            end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                            if end_dt.date() <= datetime.now().date():
                                has_expired = True
                                break
                        except ValueError:
                            pass
                if has_expired:
                    self.acolyte_listbox.itemconfig(i, foreground="#B8860B")  # Dark yellow
                else:
                    self.acolyte_listbox.itemconfig(i, foreground="red")

        # Restaura seleção
        if sel_id:
            for i, ac in enumerate(sorted_acs):
                if ac.id == sel_id:
                    self.acolyte_listbox.selection_set(i)
                    break

    def _on_acolyte_select(self, event=None):
        # Clean up overview if visible
        if hasattr(self, '_overview_frame') and self._overview_frame:
            self._overview_frame.destroy()
            self._overview_frame = None
        sel = self.acolyte_listbox.curselection()
        if not sel:
            self._hide_detail()
            self._current_acolyte = None
            return
        idx = sel[0]
        sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
        if idx < len(sorted_acs):
            self._current_acolyte = sorted_acs[idx]
            self._show_acolyte_detail()

    def _show_detail(self):
        self.no_selection_label.pack_forget()
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    def _hide_detail(self):
        self.detail_frame.pack_forget()
        self.no_selection_label.pack(pady=20)

    def _show_acolyte_detail(self):
        ac = self._current_acolyte
        if not ac:
            return
        self._show_detail()

        # Check for expired suspensions
        self._check_suspension_expiry(ac)

        susp_text = ""
        if ac.is_suspended:
            # Check if any active suspension has expired end_date
            # Uses <= so suspension is flagged on its end_date (the date is "reached")
            has_expired = False
            for s in ac.suspensions:
                if s.is_active and s.end_date:
                    try:
                        end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                        if end_dt.date() <= datetime.now().date():
                            has_expired = True
                            break
                    except ValueError:
                        pass
            if has_expired:
                susp_text = " 🟡 LEVANTAR SUSPENSÃO"
            else:
                susp_text = " 🔴 SUSPENSO"

        self.name_label.config(text=f"{ac.name}{susp_text}")
        self.summary_label.config(
            text=(
                f"Escalas: {ac.times_scheduled}  |  Faltas: {ac.absence_count}  |  "
                f"Suspensões: {ac.suspension_count}  |  Bônus: {ac.bonus_count}"
            )
        )
        self.bonus_direct_var.set(str(ac.bonus_count))

        # Atualiza as tabelas
        self._refresh_tree(self._tree_schedule, [
            (e.date, e.day, e.time, e.description or "-") for e in ac.schedule_history
        ])
        self._refresh_tree(self._tree_events, [
            (e.name, e.date, e.time or "-") for e in ac.event_history
        ])
        self._refresh_tree(self._tree_absences, [
            (a.date, a.description or "-") for a in ac.absences
        ])
        self._refresh_tree(self._tree_suspensions, [
            (s.reason, s.start_date, s.end_date or "-", s.duration, "Sim" if s.is_active else "Não")
            for s in ac.suspensions
        ])
        # Highlight expired suspensions in yellow
        for i, s in enumerate(ac.suspensions):
            if s.is_active and s.end_date:
                try:
                    end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                    if end_dt.date() <= datetime.now().date():
                        items = self._tree_suspensions.get_children()
                        if i < len(items):
                            self._tree_suspensions.tag_configure("expired", background="#FFFF99")
                            self._tree_suspensions.item(items[i], tags=("expired",))
                except ValueError:
                    pass

        self._refresh_tree(self._tree_bonus, [
            ("Ganho" if b.type == "earn" else "Usado", str(b.amount), b.description or "-", b.date)
            for b in ac.bonus_movements
        ])

    def _refresh_tree(self, tree: ttk.Treeview, rows: list):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)

    def _add_acolyte(self):
        dialog = AddMultipleAcolytesDialog(self.app.root)
        if not dialog.result:
            return
        
        names = dialog.result
        added_count = 0
        duplicates = []
        
        for name in names:
            name = name.strip()
            if not name:
                continue
            
            # Check if already exists
            existing = [a for a in self.app.acolytes if a.name.lower() == name.lower()]
            if existing:
                duplicates.append(name)
                continue
            
            # Add new acolyte
            ac = Acolyte(id=str(uuid.uuid4()), name=name)
            self.app.acolytes.append(ac)
            added_count += 1
        
        # Refresh the UI
        if added_count > 0:
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()
        
        # Show summary
        if added_count > 0 and duplicates:
            messagebox.showinfo(
                "Concluído",
                f"{added_count} acólito(s) adicionado(s) com sucesso.\n\n"
                f"Nomes duplicados ignorados: {', '.join(duplicates)}",
                parent=self.app.root
            )
        elif added_count > 0:
            messagebox.showinfo(
                "Sucesso",
                f"{added_count} acólito(s) adicionado(s) com sucesso!",
                parent=self.app.root
            )
        elif duplicates:
            messagebox.showwarning(
                "Aviso",
                f"Todos os nomes já existem no sistema:\n{', '.join(duplicates)}",
                parent=self.app.root
            )

    def _remove_acolyte(self):
        sel = self.acolyte_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um acólito para remover.")
            return
        idx = sel[0]
        sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
        if idx >= len(sorted_acs):
            return
        ac = sorted_acs[idx]
        if not messagebox.askyesno("Confirmar", f"Remover o acólito '{ac.name}'?"):
            return
        self.app.acolytes.remove(ac)
        self._current_acolyte = None
        self._hide_detail()
        self.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.save()

    def _suspend(self):
        if not self._current_acolyte:
            return
        dlg = SuspendDialog(self.app.root)
        if dlg.result:
            reason, start, duration, end_date = dlg.result
            susp = Suspension(
                id=str(uuid.uuid4()),
                reason=reason,
                start_date=start,
                duration=duration,
                end_date=end_date,
                is_active=True,
            )
            ac = self._current_acolyte
            ac.suspensions.append(susp)
            ac.is_suspended = True
            self._show_acolyte_detail()
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

    def _lift_suspension(self):
        if not self._current_acolyte:
            return
        ac = self._current_acolyte
        active_suspensions = [s for s in ac.suspensions if s.is_active]
        if not active_suspensions:
            messagebox.showinfo("Aviso", f"{ac.name} não possui suspensões ativas.")
            return
        dlg = SelectSuspensionsDialog(self.app.root, active_suspensions)
        if dlg.result:
            for susp in dlg.result:
                susp.is_active = False
            # Check if any active suspensions remain
            ac.is_suspended = any(s.is_active for s in ac.suspensions)
            self._show_acolyte_detail()
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

    def _add_absence(self):
        if not self._current_acolyte:
            return
        dlg = AddAbsenceDialog(self.app.root)
        if dlg.result:
            date, desc = dlg.result
            absence = Absence(id=str(uuid.uuid4()), date=date, description=desc)
            self._current_acolyte.absences.append(absence)
            self._show_acolyte_detail()
            self.app.save()

    def _give_bonus(self):
        if not self._current_acolyte:
            return
        dlg = BonusDialog(self.app.root, "earn")
        if dlg.result:
            amount, desc = dlg.result
            ac = self._current_acolyte
            ac.bonus_count += amount
            movement = BonusMovement(
                id=str(uuid.uuid4()),
                type="earn",
                amount=amount,
                description=desc,
                date=today_str(),
            )
            ac.bonus_movements.append(movement)
            self._show_acolyte_detail()
            self.app.save()

    def _use_bonus(self):
        if not self._current_acolyte:
            return
        ac = self._current_acolyte
        if ac.bonus_count <= 0:
            messagebox.showinfo("Aviso", f"{ac.name} não possui bônus.")
            return
        dlg = BonusDialog(self.app.root, "use")
        if dlg.result:
            amount, desc = dlg.result
            if amount > ac.bonus_count:
                messagebox.showwarning("Aviso", f"Saldo insuficiente. {ac.name} tem {ac.bonus_count} bônus.")
                return
            ac.bonus_count -= amount
            movement = BonusMovement(
                id=str(uuid.uuid4()),
                type="use",
                amount=amount,
                description=desc,
                date=today_str(),
            )
            ac.bonus_movements.append(movement)
            self._show_acolyte_detail()
            self.app.save()

    def _set_bonus_direct(self):
        if not self._current_acolyte:
            return
        try:
            new_val = int(self.bonus_direct_var.get().strip())
        except (ValueError, tk.TclError):
            return
        if new_val < 0:
            new_val = 0
        self._current_acolyte.bonus_count = new_val
        self.summary_label.config(
            text=(
                f"Escalas: {self._current_acolyte.times_scheduled}  |  "
                f"Faltas: {self._current_acolyte.absence_count}  |  "
                f"Suspensões: {self._current_acolyte.suspension_count}  |  "
                f"Bônus: {self._current_acolyte.bonus_count}"
            )
        )
        self.app.save()

    def _check_suspension_expiry(self, ac):
        """Check if any suspension end_date has been reached."""
        for s in ac.suspensions:
            if s.is_active and s.end_date:
                try:
                    end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                    if end_dt.date() <= datetime.now().date():
                        # Mark visually but don't auto-deactivate
                        pass
                except ValueError:
                    pass

    def _edit_suspension(self):
        """Edit the selected suspension."""
        if not self._current_acolyte:
            return
        sel = self._tree_suspensions.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma suspensão para editar.")
            return
        idx = self._tree_suspensions.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.suspensions):
            return
        susp = ac.suspensions[idx]
        dlg = EditSuspensionDialog(self.app.root, susp)
        if dlg.result:
            susp.reason = dlg.result["reason"]
            susp.start_date = dlg.result["start_date"]
            susp.end_date = dlg.result["end_date"]
            susp.duration = dlg.result["duration"]
            susp.is_active = dlg.result["is_active"]
            ac.is_suspended = any(s.is_active for s in ac.suspensions)
            self._show_acolyte_detail()
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

    def _delete_suspension(self):
        """Delete the selected suspension."""
        if not self._current_acolyte:
            return
        sel = self._tree_suspensions.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma suspensão para excluir.")
            return
        idx = self._tree_suspensions.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.suspensions):
            return
        susp = ac.suspensions[idx]
        if not messagebox.askyesno("Confirmar", f"Excluir a suspensão '{susp.reason}'?"):
            return
        ac.suspensions.pop(idx)
        ac.is_suspended = any(s.is_active for s in ac.suspensions)
        self._show_acolyte_detail()
        self.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.save()

    def _delete_schedule_entry(self):
        """Delete the selected schedule history entry."""
        if not self._current_acolyte:
            return
        sel = self._tree_schedule.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma entrada de escala para excluir.")
            return
        idx = self._tree_schedule.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.schedule_history):
            return
        entry = ac.schedule_history[idx]
        if not messagebox.askyesno("Confirmar", f"Excluir entrada de escala ({entry.date} {entry.time})?"):
            return
        ac.schedule_history.pop(idx)
        if ac.times_scheduled > 0:
            ac.times_scheduled -= 1
        self._show_acolyte_detail()
        self.app.save()

    def _delete_event_entry(self):
        """Delete the selected event history entry."""
        if not self._current_acolyte:
            return
        sel = self._tree_events.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma entrada de evento para excluir.")
            return
        idx = self._tree_events.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.event_history):
            return
        entry = ac.event_history[idx]
        if not messagebox.askyesno("Confirmar", f"Excluir entrada de evento '{entry.name}'?"):
            return
        ac.event_history.pop(idx)
        self._show_acolyte_detail()
        self.app.save()

    def _show_overview_table(self):
        """Show an overview table of all acolytes in the main panel."""
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        # Show the overview in the detail panel
        self._current_acolyte = None
        self.acolyte_listbox.selection_clear(0, tk.END)
        self.no_selection_label.pack_forget()
        self.detail_frame.pack_forget()

        # Remove existing overview if any
        if hasattr(self, '_overview_frame') and self._overview_frame:
            self._overview_frame.destroy()

        self._overview_frame = ttk.Frame(self.right)
        self._overview_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            self._overview_frame, text="📊 Visão Geral dos Acólitos",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor="w", pady=(4, 8))

        tree_frame = ttk.Frame(self._overview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("Nome", "Escalas", "Eventos", "Faltas", "Suspensões", "Bônus", "Status")
        overview_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            yscrollcommand=sb.set
        )
        sb.config(command=overview_tree.yview)

        widths = [160, 70, 70, 60, 80, 60, 100]
        for col, w in zip(columns, widths):
            overview_tree.heading(col, text=col)
            overview_tree.column(col, width=w, minwidth=40)

        overview_tree.tag_configure("suspended", background="#FFCCCC")
        overview_tree.tag_configure("expiring", background="#FFFFCC")

        sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
        for ac in sorted_acs:
            status = "Ativo"
            tag = ""
            if ac.is_suspended:
                # Check for expiring suspensions
                has_expired = False
                for s in ac.suspensions:
                    if s.is_active and s.end_date:
                        try:
                            end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                            if end_dt.date() <= datetime.now().date():
                                has_expired = True
                                break
                        except ValueError:
                            pass
                if has_expired:
                    status = "Levantar Suspensão"
                    tag = "expiring"
                else:
                    status = "Suspenso"
                    tag = "suspended"

            overview_tree.insert("", tk.END, values=(
                ac.name,
                ac.times_scheduled,
                len(ac.event_history),
                ac.absence_count,
                ac.suspension_count,
                ac.bonus_count,
                status,
            ), tags=(tag,) if tag else ())

        overview_tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(
            self._overview_frame, text="Fechar Visão Geral",
            command=self._close_overview
        ).pack(pady=8)

    def _close_overview(self):
        """Close the overview table and restore the normal view."""
        if hasattr(self, '_overview_frame') and self._overview_frame:
            self._overview_frame.destroy()
            self._overview_frame = None
        self.no_selection_label.pack(pady=20)

    def _close_semester(self):
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        if not messagebox.askyesno(
            "Fechar Semestre",
            "Isso vai resetar as faltas de todos os acólitos.\nDeseja continuar?",
        ):
            return
        reset_bonus = messagebox.askyesno(
            "Bônus", "Deseja também resetar os bônus de todos os acólitos?"
        )
        for ac in self.app.acolytes:
            ac.absences.clear()
            if reset_bonus:
                ac.bonus_count = 0
                ac.bonus_movements.clear()
        if self._current_acolyte:
            self._show_acolyte_detail()
        self.app.save()
        messagebox.showinfo("Concluído", "Semestre fechado com sucesso!")

    def _generate_report(self):
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Salvar relatório como",
            initialfile="relatorio_acolitos.pdf",
        )
        if not path:
            return
        try:
            sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
            report_generator.generate_report(sorted_acs, path)
            if messagebox.askyesno("Sucesso", f"Relatório gerado em:\n{path}\n\nDeseja abrir o arquivo?"):
                self._open_file(path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{e}")

    def _open_file(self, path: str):
        """Abre o arquivo com o programa padrão do sistema."""
        try:
            if sys.platform.startswith("darwin"):
                subprocess.call(["open", path])
            elif sys.platform.startswith("win"):
                subprocess.run(["cmd", "/c", "start", "", path], shell=False)
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            pass



# ---------------------------------------------------------------------------
# Aba 4: Histórico
# ---------------------------------------------------------------------------

class HistoryTab(ttk.Frame):
    """Aba de histórico de escalas geradas e eventos finalizados."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        self._sched_frame = ttk.Frame(nb)
        self._event_frame = ttk.Frame(nb)
        nb.add(self._sched_frame, text="📅 Escalas Geradas")
        nb.add(self._event_frame, text="⛪ Eventos Finalizados")

        self._build_schedule_history()
        self._build_event_history()

    def _build_schedule_history(self):
        paned = tk.PanedWindow(self._sched_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(left, text="Escalas Geradas", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._sched_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._sched_listbox.yview)
        self._sched_listbox.bind("<<ListboxSelect>>", self._on_sched_select)

        ttk.Button(left, text="✏️ Editar Escala", command=self._edit_schedule).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(left, text="🗑️ Excluir Escala", command=self._delete_schedule).pack(
            fill=tk.X, pady=4
        )

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._sched_detail_label = ttk.Label(
            right, text="Selecione uma escala para ver os detalhes.", foreground="gray"
        )
        self._sched_detail_label.pack(pady=20)

        self._sched_detail_frame = ttk.Frame(right)

        ttk.Label(
            self._sched_detail_frame, text="Texto da Escala:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        txt_frame = ttk.Frame(self._sched_detail_frame)
        txt_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(txt_frame)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_text = tk.Text(
            txt_frame, width=50, height=16, yscrollcommand=sb2.set,
            state=tk.DISABLED, font=("Courier", 9)
        )
        self._sched_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.config(command=self._sched_text.yview)

        ttk.Label(
            self._sched_detail_frame, text="Slots:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(6, 2))

        slot_frame = ttk.Frame(self._sched_detail_frame)
        slot_frame.pack(fill=tk.X)
        sb3 = ttk.Scrollbar(slot_frame, orient=tk.VERTICAL)
        sb3.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_tree = ttk.Treeview(
            slot_frame,
            columns=("Data", "Dia", "Hora", "Descrição", "Acólitos"),
            show="headings",
            height=6,
            yscrollcommand=sb3.set,
        )
        sb3.config(command=self._sched_tree.yview)
        for col, w in [("Data", 70), ("Dia", 100), ("Hora", 60), ("Descrição", 140), ("Acólitos", 180)]:
            self._sched_tree.heading(col, text=col)
            self._sched_tree.column(col, width=w, minwidth=40)
        self._sched_tree.pack(fill=tk.X, expand=False)

    def _build_event_history(self):
        paned = tk.PanedWindow(self._event_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(left, text="Eventos Finalizados", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._ev_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._ev_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._ev_listbox.yview)
        self._ev_listbox.bind("<<ListboxSelect>>", self._on_ev_select)

        ttk.Button(left, text="🗑️ Excluir Evento", command=self._delete_event_batch).pack(
            fill=tk.X, pady=4
        )

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._ev_detail_label = ttk.Label(
            right, text="Selecione um lote de eventos para ver os detalhes.", foreground="gray"
        )
        self._ev_detail_label.pack(pady=20)

        self._ev_detail_frame = ttk.Frame(right)
        ttk.Label(
            self._ev_detail_frame, text="Eventos:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        ev_frame = ttk.Frame(self._ev_detail_frame)
        ev_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(ev_frame, orient=tk.VERTICAL)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._ev_tree = ttk.Treeview(
            ev_frame,
            columns=("Nome", "Data", "Hora", "Participantes"),
            show="headings",
            yscrollcommand=sb2.set,
        )
        sb2.config(command=self._ev_tree.yview)
        for col, w in [("Nome", 160), ("Data", 70), ("Hora", 60), ("Participantes", 200)]:
            self._ev_tree.heading(col, text=col)
            self._ev_tree.column(col, width=w, minwidth=40)
        self._ev_tree.pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """Atualiza ambas as listas."""
        self._refresh_sched_list()
        self._refresh_ev_list()

    def _refresh_sched_list(self):
        self._sched_listbox.delete(0, tk.END)
        for gs in self.app.generated_schedules:
            slots_count = len(gs.slots)
            self._sched_listbox.insert(
                tk.END, f"{gs.generated_at} ({slots_count} horário(s))"
            )

    def _refresh_ev_list(self):
        self._ev_listbox.delete(0, tk.END)
        for fb in self.app.finalized_event_batches:
            count = len(fb.entries)
            self._ev_listbox.insert(tk.END, f"{fb.finalized_at} ({count} evento(s))")

    def _on_sched_select(self, event=None):
        sel = self._sched_listbox.curselection()
        if not sel:
            self._sched_detail_label.pack(pady=20)
            self._sched_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        self._sched_detail_label.pack_forget()
        self._sched_detail_frame.pack(fill=tk.BOTH, expand=True)

        self._sched_text.config(state=tk.NORMAL)
        self._sched_text.delete("1.0", tk.END)
        self._sched_text.insert(tk.END, gs.schedule_text)
        self._sched_text.config(state=tk.DISABLED)

        self._sched_tree.delete(*self._sched_tree.get_children())
        for slot in gs.slots:
            names = []
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    names.append(ac.name)
            self._sched_tree.insert(
                "", tk.END,
                values=(slot.date, slot.day, slot.time, slot.description or "-", ", ".join(names) or "-")
            )

    def _on_ev_select(self, event=None):
        sel = self._ev_listbox.curselection()
        if not sel:
            self._ev_detail_label.pack(pady=20)
            self._ev_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self.app.finalized_event_batches):
            return
        fb = self.app.finalized_event_batches[idx]
        self._ev_detail_label.pack_forget()
        self._ev_detail_frame.pack(fill=tk.BOTH, expand=True)

        self._ev_tree.delete(*self._ev_tree.get_children())
        for entry in fb.entries:
            names = []
            for aid in entry.participating_acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    names.append(ac.name)
            self._ev_tree.insert(
                "", tk.END,
                values=(entry.name, entry.date, entry.time or "-", ", ".join(names) or "-")
            )

    def _edit_schedule(self):
        """Load a generated schedule back into the schedule tab for editing."""
        sel = self._sched_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma escala para editar.")
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        if not messagebox.askyesno(
            "Editar Escala",
            f"Deseja carregar a escala de {gs.generated_at} para edição?\n\n"
            "As contagens dos acólitos serão revertidas e a escala será movida para a aba de criação.\n"
            "Horários existentes na aba de criação serão mantidos.",
        ):
            return

        # Reverse acolyte changes
        slot_ids = {s.slot_id for s in gs.slots}
        for slot in gs.slots:
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    if ac.times_scheduled > 0:
                        ac.times_scheduled -= 1
                    ac.schedule_history = [
                        e for e in ac.schedule_history if e.schedule_id not in slot_ids
                    ]

        # Create schedule slots from the snapshot
        for snap in gs.slots:
            slot = ScheduleSlot(
                id=snap.slot_id,
                date=snap.date,
                day=snap.day,
                time=snap.time,
                description=snap.description,
                acolyte_ids=list(snap.acolyte_ids),
            )
            self.app.schedule_slots.append(slot)

        # Remove from generated schedules
        self.app.generated_schedules.pop(idx)
        self.app.save()

        # Refresh UI
        self._refresh_sched_list()
        self._sched_detail_label.pack(pady=20)
        self._sched_detail_frame.pack_forget()
        self.app.schedule_tab.load_slots_from_data()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()

        # Switch to schedule tab
        self.app.notebook.select(self.app.schedule_tab)
        messagebox.showinfo("Concluído", "Escala carregada para edição na aba 'Criar Escala'.")

    def _delete_schedule(self):
        sel = self._sched_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma escala para excluir.")
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir a escala de {gs.generated_at}?\n\n"
            "Isso reverterá as contagens de escalas dos acólitos envolvidos.",
        ):
            return
        # Reverse acolyte changes: decrement times_scheduled and remove schedule_history entries
        slot_ids = {s.slot_id for s in gs.slots}
        for slot in gs.slots:
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    if ac.times_scheduled > 0:
                        ac.times_scheduled -= 1
                    ac.schedule_history = [
                        e for e in ac.schedule_history if e.schedule_id not in slot_ids
                    ]
        self.app.generated_schedules.pop(idx)
        self.app.save()
        self._refresh_sched_list()
        self._sched_detail_label.pack(pady=20)
        self._sched_detail_frame.pack_forget()
        self.app.acolytes_tab.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        messagebox.showinfo("Concluído", "Escala excluída e contagens revertidas.")

    def _delete_event_batch(self):
        sel = self._ev_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um lote de eventos para excluir.")
            return
        idx = sel[0]
        if idx >= len(self.app.finalized_event_batches):
            return
        fb = self.app.finalized_event_batches[idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o lote de eventos de {fb.finalized_at}?\n\n"
            "Isso removerá os registros de eventos dos acólitos.",
        ):
            return
        event_ids = {e.event_id for e in fb.entries}
        for ac in self.app.acolytes:
            ac.event_history = [e for e in ac.event_history if e.event_id not in event_ids]
        self.app.finalized_event_batches.pop(idx)
        self.app.save()
        self._refresh_ev_list()
        self._ev_detail_label.pack(pady=20)
        self._ev_detail_frame.pack_forget()
        self.app.acolytes_tab.refresh_list()
        messagebox.showinfo("Concluído", "Lote de eventos excluído.")


# ---------------------------------------------------------------------------
# Aplicação principal
# ---------------------------------------------------------------------------

class App:
    def __init__(self):
        self.acolytes: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []
        self.generated_schedules: List[GeneratedSchedule] = []
        self.finalized_event_batches: List[FinalizedEventBatch] = []
        self.standard_slots: List[StandardSlot] = []

        self.root = tk.Tk()
        self.root.title("Gerenciador de Acólitos")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        self._apply_theme()
        self._build_menu()
        self._build_notebook()
        self._load_data()

    def _apply_theme(self):
        style = ttk.Style(self.root)
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=[10, 4])
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"))

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Salvar", command=self.save, accelerator="Ctrl+S")
        file_menu.add_command(label="Carregar", command=self._load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Dados...", command=self._export_data)
        file_menu.add_command(label="Importar Dados...", command=self._import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)

        self.root.bind("<Control-s>", lambda e: self.save())

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.schedule_tab = ScheduleTab(self.notebook, self)
        self.events_tab = EventsTab(self.notebook, self)
        self.acolytes_tab = AcolytesTab(self.notebook, self)
        self.history_tab = HistoryTab(self.notebook, self)

        self.notebook.add(self.schedule_tab, text="📅 Criar Escala")
        self.notebook.add(self.events_tab, text="⛪ Eventos Gerais")
        self.notebook.add(self.acolytes_tab, text="👥 Acólitos")
        self.notebook.add(self.history_tab, text="📜 Histórico")

    def _load_data(self):
        result = data_manager.load_data()
        (
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
        ) = result
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data()
        self.events_tab.refresh_list()
        self.acolytes_tab.refresh_list()
        self.history_tab.refresh()

    def save(self):
        data_manager.save_data(
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
        )

    def find_acolyte(self, acolyte_id: str) -> Optional[Acolyte]:
        for ac in self.acolytes:
            if ac.id == acolyte_id:
                return ac
        return None

    def get_selected_acolyte_for_schedule(self) -> Optional[Acolyte]:
        """Retorna o acólito selecionado na aba de escalas."""
        return self.schedule_tab.get_selected_acolyte()

    def get_selected_acolytes_for_schedule(self) -> List[Acolyte]:
        """Retorna todos os acólitos selecionados na aba de escalas."""
        return self.schedule_tab.get_selected_acolytes()

    def _export_data(self):
        """Exporta todos os dados para um arquivo JSON."""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar dados como",
            initialfile="acolitos_backup.json",
        )
        if not path:
            return
        try:
            data_manager.export_to_file(
                self.acolytes,
                self.schedule_slots,
                self.general_events,
                path,
                self.generated_schedules,
                self.finalized_event_batches,
                self.standard_slots,
            )
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar dados:\n{e}")

    def _import_data(self):
        """Importa todos os dados de um arquivo JSON."""
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            title="Importar dados de",
        )
        if not path:
            return
        if not messagebox.askyesno(
            "Confirmar Importação",
            "Atenção: isso substituirá TODOS os dados atuais pelos dados do arquivo importado.\n\n"
            "Deseja continuar?",
        ):
            return
        try:
            (
                acolytes,
                schedule_slots,
                general_events,
                generated_schedules,
                finalized_event_batches,
                standard_slots,
            ) = data_manager.import_from_file(path)
            self.acolytes = acolytes
            self.schedule_slots = schedule_slots
            self.general_events = general_events
            self.generated_schedules = generated_schedules
            self.finalized_event_batches = finalized_event_batches
            self.standard_slots = standard_slots
            self.save()
            self._load_data()
            messagebox.showinfo(
                "Sucesso",
                f"Dados importados com sucesso!\n\n"
                f"{len(acolytes)} acólitos, {len(schedule_slots)} escalas, {len(general_events)} eventos.",
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao importar dados:\n{e}")

    def _show_about(self):
        messagebox.showinfo(
            "Sobre",
            "Gerenciador de Acólitos\n\n"
            "Ferramenta para gerenciar a escala de acólitos de uma igreja.\n\n"
            "Funcionalidades:\n"
            "- Criar e gerenciar escalas semanais\n"
            "- Registrar eventos gerais\n"
            "- Gerenciar acólitos (faltas, bônus, suspensões)\n"
            "- Gerar relatórios em PDF",
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
