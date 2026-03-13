"""Diálogos modais da aplicação."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from ..models import BonusMovement, StandardSlot, ScheduleSlot, Unavailability, TemporaryUnavailability, Activity
from ..utils import (
    WEEKDAYS_PT,
    detect_weekday,
    today_str,
    normalize_date,
    next_occurrence_of_day,
)
from .base import BaseDialog
from .widgets import DateEntryFrame, TimeEntryFrame


class AddAbsenceDialog(BaseDialog):
    """Diálogo para registrar uma falta."""

    def __init__(self, parent):
        super().__init__(parent, "Registrar Falta")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(
            row=1, column=1, padx=8, pady=4
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        date = normalize_date(self.date_var.get().strip())
        desc = self.desc_var.get().strip()
        if not date:
            messagebox.showwarning("Aviso", "Informe a data.", parent=self)
            return
        self.result = (date, desc)
        self.destroy()


class EditAbsenceDialog(BaseDialog):
    """Diálogo para editar uma falta."""

    def __init__(self, parent, absence):
        self._absence = absence
        super().__init__(parent, "Editar Falta")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=self._absence.date)
        DateEntryFrame(frame, textvariable=self.date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(value=self._absence.description or "")
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(
            row=1, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Não contada:").grid(row=2, column=0, sticky="w", pady=4)
        self.symbolic_var = tk.BooleanVar(value=self._absence.is_symbolic)
        ttk.Checkbutton(frame, variable=self.symbolic_var).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        date = normalize_date(self.date_var.get().strip())
        if not date:
            messagebox.showwarning("Aviso", "Informe a data.", parent=self)
            return
        self.result = {
            "date": date,
            "description": self.desc_var.get().strip(),
            "is_symbolic": self.symbolic_var.get(),
        }
        self.destroy()


class AddScheduleEntryDialog(BaseDialog):
    """Diálogo para adicionar uma entrada no histórico de escalas."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Entrada de Escala")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Horário (HH:MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Descrição:").grid(row=2, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(
            row=2, column=1, padx=8, pady=4
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        date = normalize_date(self.date_var.get().strip())
        time = self.time_var.get().strip()
        desc = self.desc_var.get().strip()
        if not date:
            messagebox.showwarning("Aviso", "Informe a data.", parent=self)
            return
        if not time:
            messagebox.showwarning("Aviso", "Informe o horário.", parent=self)
            return
        day = detect_weekday(date)
        if not day:
            messagebox.showwarning("Aviso", "Data inválida.", parent=self)
            return
        self.result = (date, day, time, desc)
        self.destroy()


class AddEventEntryDialog(BaseDialog):
    """Diálogo para adicionar uma entrada no histórico de atividades."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Entrada de Atividade")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nome da atividade:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=1, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Horário (opcional, HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        name = self.name_var.get().strip()
        date = normalize_date(self.date_var.get().strip())
        time = self.time_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Informe o nome da atividade.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data.", parent=self)
            return
        self.result = (name, date, time)
        self.destroy()


class SuspendDialog(BaseDialog):
    """Diálogo para suspender um acólito."""

    def __init__(self, parent):
        super().__init__(parent, "Suspender Acólito")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Motivo:").grid(row=0, column=0, sticky="w", pady=4)
        self.reason_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.reason_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data de início (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.start_var, width=14, date_format="DD/MM/YYYY").grid(
            row=1, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data de fim (DD/MM/YYYY):").grid(row=2, column=0, sticky="w", pady=4)
        self.end_var = tk.StringVar()
        DateEntryFrame(frame, textvariable=self.end_var, width=14, date_format="DD/MM/YYYY").grid(
            row=2, column=1, padx=8, pady=4
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        reason = self.reason_var.get().strip()
        start = normalize_date(self.start_var.get().strip())
        end_date = normalize_date(self.end_var.get().strip())
        if not reason:
            messagebox.showwarning("Aviso", "Informe o motivo.", parent=self)
            return
        self.result = (reason, start, end_date)
        self.destroy()


class SelectSuspensionsDialog(BaseDialog):
    """Diálogo para selecionar quais suspensões ativas desativar."""

    def __init__(self, parent, suspensions: list):
        self._suspensions = suspensions
        super().__init__(parent, "Selecionar Suspensões para Levantar")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecione as suspensões que deseja levantar:").pack(
            anchor="w", pady=(0, 6)
        )

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
            messagebox.showwarning(
                "Aviso", "Selecione pelo menos uma suspensão.", parent=self
            )
            return
        self.result = selected
        self.destroy()


class EditSuspensionDialog(BaseDialog):
    """Diálogo para editar uma suspensão."""

    def __init__(self, parent, suspension):
        self._suspension = suspension
        super().__init__(parent, "Editar Suspensão")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Motivo:").grid(row=0, column=0, sticky="w", pady=4)
        self.reason_var = tk.StringVar(value=self._suspension.reason)
        ttk.Entry(frame, textvariable=self.reason_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data de início:").grid(row=1, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar(value=self._suspension.start_date)
        DateEntryFrame(frame, textvariable=self.start_var, width=14, date_format="DD/MM/YYYY").grid(
            row=1, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data de fim:").grid(row=2, column=0, sticky="w", pady=4)
        self.end_var = tk.StringVar(value=self._suspension.end_date)
        DateEntryFrame(frame, textvariable=self.end_var, width=14, date_format="DD/MM/YYYY").grid(
            row=2, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Ativa:").grid(row=3, column=0, sticky="w", pady=4)
        self.active_var = tk.BooleanVar(value=self._suspension.is_active)
        ttk.Checkbutton(frame, variable=self.active_var).grid(
            row=3, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        self.result = {
            "reason": self.reason_var.get().strip(),
            "start_date": normalize_date(self.start_var.get().strip()),
            "end_date": normalize_date(self.end_var.get().strip()),
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
        ttk.Entry(frame, textvariable=self.desc_var, width=30).grid(
            row=1, column=1, padx=8, pady=4
        )

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


class EditBonusMovementDialog(BaseDialog):
    """Diálogo para editar uma movimentação de bônus."""

    def __init__(self, parent, movement: BonusMovement):
        self._movement = movement
        super().__init__(parent, "Editar Movimentação de Bônus")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tipo:").grid(row=0, column=0, sticky="w", pady=4)
        self.type_var = tk.StringVar(value=self._movement.type)
        ttk.Combobox(
            frame,
            textvariable=self.type_var,
            values=("earn", "use"),
            width=10,
            state="readonly",
        ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Quantidade:").grid(row=1, column=0, sticky="w", pady=4)
        self.amount_var = tk.StringVar(value=str(self._movement.amount))
        ttk.Spinbox(frame, from_=1, to=9999, textvariable=self.amount_var, width=8).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Descrição:").grid(row=2, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(value=self._movement.description)
        ttk.Entry(frame, textvariable=self.desc_var, width=32).grid(
            row=2, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data (DD/MM):").grid(row=3, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=self._movement.date)
        DateEntryFrame(
            frame,
            textvariable=self.date_var,
            width=10,
            date_format="DD/MM",
        ).grid(row=3, column=1, padx=8, pady=4, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        mov_type = self.type_var.get().strip()
        if mov_type not in ("earn", "use"):
            messagebox.showwarning("Aviso", "Selecione um tipo válido.", parent=self)
            return

        try:
            amount = int(self.amount_var.get().strip())
            if amount < 1:
                amount = 1
        except (ValueError, tk.TclError):
            amount = 1

        desc = self.desc_var.get().strip()
        date = normalize_date(self.date_var.get().strip())
        if not date:
            messagebox.showwarning("Aviso", "Informe uma data válida.", parent=self)
            return

        self.result = {
            "type": mov_type,
            "amount": amount,
            "description": desc,
            "date": date,
        }
        self.destroy()


class FinalizeScheduleDialog(BaseDialog):
    """Diálogo que exibe o texto gerado da escala."""

    def __init__(self, parent, text: str):
        super().__init__(parent, "Escala Gerada")
        self._text = text
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Texto da convocação:").pack(anchor="w")

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
        messagebox.showinfo(
            "Copiado", "Texto copiado para a área de transferência!", parent=self
        )


class AddEventDialog(BaseDialog):
    """Diálogo para adicionar uma atividade."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Atividade")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        self._updating_fields = False

        ttk.Label(frame, text="Nome da atividade:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Dia da semana:").grid(row=1, column=0, sticky="w", pady=4)
        self.day_var = tk.StringVar(value=WEEKDAYS_PT[datetime.now().weekday()])
        self.day_combo = ttk.Combobox(
            frame,
            textvariable=self.day_var,
            values=WEEKDAYS_PT,
            width=20,
            state="readonly",
        )
        self.day_combo.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Data (DD/MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=next_occurrence_of_day(self.day_var.get()))
        DateEntryFrame(frame, textvariable=self.date_var, width=8, date_format="DD/MM").grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        self.day_var.trace_add("write", self._on_day_change)
        self.date_var.trace_add("write", self._on_date_change)

        ttk.Label(frame, text="Horário (HH:MM):").grid(row=3, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(
            row=3, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _on_day_change(self, *_):
        if self._updating_fields:
            return
        day = self.day_var.get().strip()
        if not day:
            return
        date_for_day = next_occurrence_of_day(day)
        if not date_for_day:
            return
        self._updating_fields = True
        self.date_var.set(date_for_day)
        self._updating_fields = False

    def _on_date_change(self, *_):
        if self._updating_fields:
            return
        date = normalize_date(self.date_var.get().strip())
        if not date:
            return
        weekday = detect_weekday(date)
        if not weekday or weekday == self.day_var.get():
            return
        self._updating_fields = True
        self.day_var.set(weekday)
        self._updating_fields = False

    def _ok(self):
        name = self.name_var.get().strip()
        date = normalize_date(self.date_var.get().strip())
        if not date and self.day_var.get().strip():
            date = next_occurrence_of_day(self.day_var.get().strip())
        time = self.time_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Informe o nome da atividade.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data da atividade.", parent=self)
            return
        self.result = (name, date, time)
        self.destroy()


class AddConvocacaoGeralDialog(BaseDialog):
    """Diálogo para adicionar uma Convocação geral."""

    _last_include_as_activity: bool = True

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Convocação geral")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        self._updating_fields = False

        ttk.Label(frame, text="Nome da Convocação geral:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Dia da semana:").grid(row=1, column=0, sticky="w", pady=4)
        self.day_var = tk.StringVar(value=WEEKDAYS_PT[datetime.now().weekday()])
        self.day_combo = ttk.Combobox(
            frame,
            textvariable=self.day_var,
            values=WEEKDAYS_PT,
            width=20,
            state="readonly",
        )
        self.day_combo.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Data (DD/MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=next_occurrence_of_day(self.day_var.get()))
        DateEntryFrame(frame, textvariable=self.date_var, width=8, date_format="DD/MM").grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        self.day_var.trace_add("write", self._on_day_change)
        self.date_var.trace_add("write", self._on_date_change)

        ttk.Label(frame, text="Horário (HH:MM):").grid(row=3, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(
            row=3, column=1, padx=8, pady=4, sticky="w"
        )

        self.include_as_activity_var = tk.BooleanVar(
            value=AddConvocacaoGeralDialog._last_include_as_activity
        )
        ttk.Checkbutton(
            frame, text="Incluir como atividade", variable=self.include_as_activity_var
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        self.include_as_schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, text="Incluir como escala", variable=self.include_as_schedule_var
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _on_day_change(self, *_):
        if self._updating_fields:
            return
        day = self.day_var.get().strip()
        if not day:
            return
        date_for_day = next_occurrence_of_day(day)
        if not date_for_day:
            return
        self._updating_fields = True
        self.date_var.set(date_for_day)
        self._updating_fields = False

    def _on_date_change(self, *_):
        if self._updating_fields:
            return
        date = normalize_date(self.date_var.get().strip())
        if not date:
            return
        weekday = detect_weekday(date)
        if not weekday or weekday == self.day_var.get():
            return
        self._updating_fields = True
        self.day_var.set(weekday)
        self._updating_fields = False

    def _ok(self):
        name = self.name_var.get().strip()
        date = normalize_date(self.date_var.get().strip())
        if not date and self.day_var.get().strip():
            date = next_occurrence_of_day(self.day_var.get().strip())
        time = self.time_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Informe o nome da Convocação geral.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data da Convocação geral.", parent=self)
            return
        if not time:
            messagebox.showwarning("Aviso", "Informe o horário da Convocação geral.", parent=self)
            return
        include_activity = self.include_as_activity_var.get()
        include_schedule = self.include_as_schedule_var.get()
        if not include_activity and not include_schedule:
            messagebox.showwarning(
                "Aviso",
                "Selecione pelo menos uma opção: incluir como atividade ou como escala.",
                parent=self,
            )
            return
        AddConvocacaoGeralDialog._last_include_as_activity = include_activity
        self.result = (name, date, time, include_activity, include_schedule)
        self.destroy()


class AddMultipleAcolytesDialog(BaseDialog):
    """Diálogo para adicionar múltiplos acólitos de uma vez."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Acólitos")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Digite os nomes dos acólitos (um por linha):"
        ).pack(anchor="w", pady=(0, 4))

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

        names = []
        for line in text.split('\n'):
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


class StandardSlotsDialog(BaseDialog):
    """Diálogo para gerenciar convocação padrão."""

    def __init__(self, parent, app):
        self.app = app
        super().__init__(parent, "Gerenciar Convocação Padrão")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Itens da convocação padrão podem ser escalas normais ou atividades e são adicionados automaticamente à convocação atual.",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 6))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=sb.set, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.listbox.yview)

        self._refresh_list()

        add_frame = ttk.LabelFrame(frame, text="Adicionar Item da Convocação Padrão", padding=8)
        add_frame.pack(fill=tk.X, pady=6)

        ttk.Label(add_frame, text="Dia:").grid(row=0, column=0, sticky="w", pady=2)
        self._day_var = tk.StringVar()
        ttk.Combobox(
            add_frame, textvariable=self._day_var, values=WEEKDAYS_PT,
            width=16, state="readonly"
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

        self._is_activity_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            add_frame,
            text="É atividade",
            variable=self._is_activity_var,
            command=self._toggle_activity_options,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        self._include_in_message_var = tk.BooleanVar(value=False)
        self._include_in_message_check = ttk.Checkbutton(
            add_frame,
            text="Incluir na mensagem",
            variable=self._include_in_message_var,
        )
        self._include_in_message_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Button(add_frame, text="➕ Adicionar", command=self._add_slot).grid(
            row=5, column=0, columnspan=2, pady=6
        )

        self._toggle_activity_options()
        self._displayed_standard_slots = []

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="🗑️ Remover Selecionado", command=self._remove_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(
            btn_row, text="📋 Adicionar à Convocação Atual", command=self._add_to_schedule
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Fechar", command=self.destroy).pack(side=tk.RIGHT, padx=4)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        self._displayed_standard_slots = sorted(
            self.app.standard_slots,
            key=self._standard_slot_sort_key,
        )
        for ss in self._displayed_standard_slots:
            type_label = "Atividade" if getattr(ss, "is_activity", False) else "Horário"
            extra = " [mensagem]" if getattr(ss, "is_activity", False) and getattr(ss, "include_in_message", False) else ""
            time_text = ss.time or "sem hora"
            self.listbox.insert(tk.END, f"{type_label}: {ss.day} {time_text} - {ss.description}{extra}")

    def _standard_slot_sort_key(self, slot: StandardSlot):
        try:
            day_idx = WEEKDAYS_PT.index(slot.day)
        except ValueError:
            day_idx = len(WEEKDAYS_PT)

        time_text = (slot.time or "").strip()
        time_rank = 1
        time_sort = "99:99"
        if time_text:
            time_rank = 0
            time_sort = time_text

        return day_idx, time_rank, time_sort, (slot.description or "").lower(), slot.id

    def _toggle_activity_options(self):
        if self._is_activity_var.get():
            self._include_in_message_check.state(["!disabled"])
        else:
            self._include_in_message_var.set(False)
            self._include_in_message_check.state(["disabled"])

    def _add_slot(self):
        day = self._day_var.get().strip()
        time = self._time_var.get().strip()
        desc = self._desc_var.get().strip()
        if not day:
            messagebox.showwarning("Aviso", "Selecione o dia da semana.", parent=self)
            return
        ss = StandardSlot(
            id=str(uuid.uuid4()),
            day=day,
            time=time,
            description=desc,
            is_activity=self._is_activity_var.get(),
            include_in_message=self._include_in_message_var.get(),
        )
        self.app.standard_slots.append(ss)
        self.app.save()
        self._refresh_list()

    def _remove_slot(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um item da convocação padrão.", parent=self)
            return
        idx = sel[0]
        if idx < len(self._displayed_standard_slots):
            selected_slot = self._displayed_standard_slots[idx]
            self.app.standard_slots = [
                ss for ss in self.app.standard_slots
                if ss.id != selected_slot.id
            ]
            self.app.save()
            self._refresh_list()

    def _add_to_schedule(self):
        ordered_slots = sorted(self.app.standard_slots, key=self._standard_slot_sort_key)
        if not ordered_slots:
            messagebox.showinfo("Aviso", "Nenhum item da convocação padrão cadastrado.", parent=self)
            return
        added_schedule_items = 0
        added_activity_items = 0
        for ss in ordered_slots:
            auto_date = next_occurrence_of_day(ss.day)
            if getattr(ss, "is_activity", False):
                event = Activity(
                    id=str(uuid.uuid4()),
                    name=ss.description,
                    date=auto_date,
                    time=ss.time,
                    include_in_message=getattr(ss, "include_in_message", False),
                )
                self.app.general_events.append(event)
                added_activity_items += 1
            else:
                slot = ScheduleSlot(
                    id=str(uuid.uuid4()), date=auto_date, day=ss.day,
                    time=ss.time, description=ss.description,
                )
                self.app.schedule_slots.append(slot)
                added_schedule_items += 1
        self.app.schedule_tab.load_slots_from_data()
        self.app.events_tab.refresh_list()
        self.app.save()
        messagebox.showinfo(
            "Concluído",
            f"{added_schedule_items} escala(s) e {added_activity_items} atividade(s) da convocação padrão adicionados à convocação atual.\n"
            "Datas preenchidas automaticamente.",
            parent=self,
        )


class AddUnavailabilityDialog(BaseDialog):
    """Diálogo para adicionar uma indisponibilidade a um acólito."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Indisponibilidade")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Dia da semana:").grid(row=0, column=0, sticky="w", pady=4)
        self.day_var = tk.StringVar()
        ttk.Combobox(
            frame, textvariable=self.day_var, values=WEEKDAYS_PT, width=18, state="readonly"
        ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Hora início (HH:MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.start_var, width=8).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Hora fim (HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.end_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.end_var, width=8).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        day = self.day_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        if not day:
            messagebox.showwarning("Aviso", "Selecione o dia da semana.", parent=self)
            return
        if not start or not end:
            messagebox.showwarning("Aviso", "Informe os horários de início e fim.", parent=self)
            return
        try:
            sh, sm = map(int, start.split(":"))
            eh, em = map(int, end.split(":"))
            if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
                raise ValueError
            start = f"{sh:02d}:{sm:02d}"
            end = f"{eh:02d}:{em:02d}"
            if start >= end:
                messagebox.showwarning("Aviso", "O horário de início deve ser anterior ao fim.", parent=self)
                return
        except (ValueError, AttributeError):
            messagebox.showwarning("Aviso", "Informe horários válidos no formato HH:MM.", parent=self)
            return
        self.result = (day, start, end)
        self.destroy()


class AddTemporaryUnavailabilityDialog(BaseDialog):
    """Diálogo para adicionar uma indisponibilidade temporária por intervalo de datas."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Indisponibilidade Temporária")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Data início (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.start_date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.start_date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Data fim (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=4)
        self.end_date_var = tk.StringVar(value=today_str())
        DateEntryFrame(frame, textvariable=self.end_date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Label(
            frame,
            text="Horário (deixe em branco para o dia todo):",
            foreground="#555555",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 2))

        ttk.Label(frame, text="Hora início (HH:MM):").grid(row=4, column=0, sticky="w", pady=4)
        self.start_time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.start_time_var, width=8).grid(
            row=4, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Hora fim (HH:MM):").grid(row=5, column=0, sticky="w", pady=4)
        self.end_time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.end_time_var, width=8).grid(
            row=5, column=1, padx=8, pady=4, sticky="w"
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        start_date = normalize_date(self.start_date_var.get().strip())
        end_date = normalize_date(self.end_date_var.get().strip())
        if not start_date or not end_date:
            messagebox.showwarning("Aviso", "Informe as datas de início e fim.", parent=self)
            return
        try:
            sd = datetime.strptime(start_date, "%d/%m/%Y")
            ed = datetime.strptime(end_date, "%d/%m/%Y")
            if ed < sd:
                messagebox.showwarning("Aviso", "A data de fim deve ser igual ou posterior à de início.", parent=self)
                return
        except ValueError:
            messagebox.showwarning("Aviso", "Datas inválidas. Use o formato DD/MM/YYYY.", parent=self)
            return

        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()

        # Validate times only if at least one is provided
        if start_time or end_time:
            if not start_time or not end_time:
                messagebox.showwarning("Aviso", "Informe ambos os horários ou deixe os dois em branco.", parent=self)
                return
            try:
                sh, sm = map(int, start_time.split(":"))
                eh, em = map(int, end_time.split(":"))
                if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
                    raise ValueError
                start_time = f"{sh:02d}:{sm:02d}"
                end_time = f"{eh:02d}:{em:02d}"
                if start_time >= end_time:
                    messagebox.showwarning("Aviso", "O horário de início deve ser anterior ao fim.", parent=self)
                    return
            except (ValueError, AttributeError):
                messagebox.showwarning("Aviso", "Horários inválidos. Use o formato HH:MM.", parent=self)
                return

        self.result = (start_date, end_date, start_time, end_time)
        self.destroy()


class EditUnavailabilityDialog(BaseDialog):
    """Diálogo para editar uma indisponibilidade (semanal ou temporária)."""

    def __init__(self, parent, item):
        self._item = item
        self._is_temporary = isinstance(item, TemporaryUnavailability)
        title = "Editar Indisponibilidade Temporária" if self._is_temporary else "Editar Indisponibilidade"
        super().__init__(parent, title)
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        if self._is_temporary:
            self._build_temporary(frame)
        else:
            self._build_regular(frame)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=self._btn_row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _build_regular(self, frame):
        ttk.Label(frame, text="Dia da semana:").grid(row=0, column=0, sticky="w", pady=4)
        self.day_var = tk.StringVar(value=self._item.day)
        ttk.Combobox(
            frame, textvariable=self.day_var, values=WEEKDAYS_PT, width=18, state="readonly"
        ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Hora início (HH:MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.start_time_var = tk.StringVar(value=self._item.start_time)
        TimeEntryFrame(frame, textvariable=self.start_time_var, width=8).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Hora fim (HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.end_time_var = tk.StringVar(value=self._item.end_time)
        TimeEntryFrame(frame, textvariable=self.end_time_var, width=8).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )
        self._btn_row = 3

    def _build_temporary(self, frame):
        ttk.Label(frame, text="Data início (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", pady=4)
        self.start_date_var = tk.StringVar(value=self._item.start_date)
        DateEntryFrame(frame, textvariable=self.start_date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Data fim (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=4)
        self.end_date_var = tk.StringVar(value=self._item.end_date)
        DateEntryFrame(frame, textvariable=self.end_date_var, width=14, date_format="DD/MM/YYYY").grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Label(
            frame,
            text="Horário (deixe em branco para o dia todo):",
            foreground="#555555",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 2))

        ttk.Label(frame, text="Hora início (HH:MM):").grid(row=4, column=0, sticky="w", pady=4)
        self.start_time_var = tk.StringVar(value=self._item.start_time)
        TimeEntryFrame(frame, textvariable=self.start_time_var, width=8).grid(
            row=4, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Hora fim (HH:MM):").grid(row=5, column=0, sticky="w", pady=4)
        self.end_time_var = tk.StringVar(value=self._item.end_time)
        TimeEntryFrame(frame, textvariable=self.end_time_var, width=8).grid(
            row=5, column=1, padx=8, pady=4, sticky="w"
        )
        self._btn_row = 6

    def _ok(self):
        if self._is_temporary:
            self._ok_temporary()
        else:
            self._ok_regular()

    def _ok_regular(self):
        day = self.day_var.get().strip()
        start = self.start_time_var.get().strip()
        end = self.end_time_var.get().strip()
        if not day:
            messagebox.showwarning("Aviso", "Selecione o dia da semana.", parent=self)
            return
        if not start or not end:
            messagebox.showwarning("Aviso", "Informe os horários de início e fim.", parent=self)
            return
        try:
            sh, sm = map(int, start.split(":"))
            eh, em = map(int, end.split(":"))
            if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
                raise ValueError
            start = f"{sh:02d}:{sm:02d}"
            end = f"{eh:02d}:{em:02d}"
            if start >= end:
                messagebox.showwarning("Aviso", "O horário de início deve ser anterior ao fim.", parent=self)
                return
        except (ValueError, AttributeError):
            messagebox.showwarning("Aviso", "Informe horários válidos no formato HH:MM.", parent=self)
            return
        self.result = ("regular", day, start, end)
        self.destroy()

    def _ok_temporary(self):
        start_date = normalize_date(self.start_date_var.get().strip())
        end_date = normalize_date(self.end_date_var.get().strip())
        if not start_date or not end_date:
            messagebox.showwarning("Aviso", "Informe as datas de início e fim.", parent=self)
            return
        try:
            sd = datetime.strptime(start_date, "%d/%m/%Y")
            ed = datetime.strptime(end_date, "%d/%m/%Y")
            if ed < sd:
                messagebox.showwarning("Aviso", "A data de fim deve ser igual ou posterior à de início.", parent=self)
                return
        except ValueError:
            messagebox.showwarning("Aviso", "Datas inválidas. Use o formato DD/MM/YYYY.", parent=self)
            return

        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()
        if start_time or end_time:
            if not start_time or not end_time:
                messagebox.showwarning("Aviso", "Informe ambos os horários ou deixe os dois em branco.", parent=self)
                return
            try:
                sh, sm = map(int, start_time.split(":"))
                eh, em = map(int, end_time.split(":"))
                if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
                    raise ValueError
                start_time = f"{sh:02d}:{sm:02d}"
                end_time = f"{eh:02d}:{em:02d}"
                if start_time >= end_time:
                    messagebox.showwarning("Aviso", "O horário de início deve ser anterior ao fim.", parent=self)
                    return
            except (ValueError, AttributeError):
                messagebox.showwarning("Aviso", "Horários inválidos. Use o formato HH:MM.", parent=self)
                return

        self.result = ("temporary", start_date, end_date, start_time, end_time)
        self.destroy()


class GeneralEventUnavailabilityDialog(BaseDialog):
    """Lista acólitos com conflito de indisponibilidade para uma Convocação geral."""

    def __init__(self, parent, event_name, event_time, event_day, conflicting_acolytes):
        self._event_name = event_name
        self._event_time = event_time
        self._event_day = event_day
        self._conflicting_acolytes = conflicting_acolytes
        super().__init__(parent, "Aviso de Indisponibilidade")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text=(
                f"Os acólitos abaixo têm indisponibilidade em\n"
                f"{self._event_day} às {self._event_time} para '{self._event_name}'.\n\n"
                "Marque os que deseja incluir mesmo assim:"
            ),
            justify="left",
            foreground="#8B0000",
        ).pack(anchor="w", pady=(0, 8))

        self._include_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Incluir todos", variable=self._include_all_var,
            command=self._toggle_all
        ).pack(anchor="w", pady=(0, 4))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._vars = []
        for ac in self._conflicting_acolytes:
            var = tk.BooleanVar(value=False)
            self._vars.append((ac, var))
            ttk.Checkbutton(list_frame, text=ac.name, variable=var).pack(anchor="w", padx=4, pady=1)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_frame, text="Cancelar (incluir nenhum)", command=self._cancel
        ).pack(side=tk.LEFT, padx=4)

    def _toggle_all(self):
        val = self._include_all_var.get()
        for _, var in self._vars:
            var.set(val)

    def _ok(self):
        # Returns list of acolytes to EXCLUDE (those not checked)
        self.result = [ac for ac, var in self._vars if not var.get()]
        self.destroy()

    def _cancel(self):
        # Exclude all conflicting acolytes
        self.result = [ac for ac, _ in self._vars]
        self.destroy()


class EditGeneralEventExcludedDialog(BaseDialog):
    """Edita quais acólitos serão excluídos de uma Convocação geral."""

    def __init__(
        self,
        parent,
        acolytes,
        excluded_ids,
        suspended_locked_ids=None,
    ):
        self._acolytes = acolytes
        self._excluded_ids = set(excluded_ids or [])
        self._suspended_locked_ids = set(suspended_locked_ids or [])
        super().__init__(parent, "Editar Excluídos - Convocação geral")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Marque os acólitos que devem ficar excluídos desta Convocação geral:",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        if self._suspended_locked_ids:
            ttk.Label(
                frame,
                text="(suspensos estão bloqueados enquanto a configuração de inclusão estiver desativada)",
                foreground="gray",
                justify="left",
            ).pack(anchor="w", pady=(0, 6))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._vars = []
        for ac in self._acolytes:
            locked = ac.id in self._suspended_locked_ids
            default_checked = locked or (ac.id in self._excluded_ids)
            var = tk.BooleanVar(value=default_checked)
            self._vars.append((ac, var, locked))
            suffix = " (susp.)" if locked else ""
            cb = ttk.Checkbutton(list_frame, text=f"{ac.name}{suffix}", variable=var)
            cb.pack(anchor="w", padx=4, pady=1)
            if locked:
                cb.state(["disabled"])

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        selected_ids = []
        for ac, var, locked in self._vars:
            if locked or var.get():
                selected_ids.append(ac.id)
        self.result = selected_ids
        self.destroy()


class EditEventParticipantsDialog(BaseDialog):
    """Edita quais acólitos estão excluídos de uma atividade."""

    def __init__(self, parent, acolytes, excluded_ids):
        self._acolytes = acolytes
        self._excluded_ids = set(excluded_ids or [])
        super().__init__(parent, "Editar Excluídos - Atividade")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Marque os acólitos que devem ficar excluídos desta atividade:",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._vars = []
        for ac in self._acolytes:
            default_checked = ac.id in self._excluded_ids
            var = tk.BooleanVar(value=default_checked)
            self._vars.append((ac, var))
            suffix = " (susp.)" if getattr(ac, "is_suspended", False) else ""
            ttk.Checkbutton(list_frame, text=f"{ac.name}{suffix}", variable=var).pack(
                anchor="w", padx=4, pady=1
            )

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        self.result = [ac.id for ac, var in self._vars if var.get()]
        self.destroy()


class CloseCicloDialog(BaseDialog):
    """Diálogo para fechar o ciclo atual."""

    def __init__(
        self,
        parent,
        initial_label: str = "",
        *,
        title_text: str = "Fechar Ciclo",
        action_text: str = "Fechar Ciclo",
        show_retention_options: bool = True,
        info_title: Optional[str] = None,
    ):
        self._initial_label = initial_label
        self._action_text = action_text
        self._show_retention_options = show_retention_options
        self._info_title = info_title
        super().__init__(parent, title_text)
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        self.save_history_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Salvar ciclo atual no histórico",
            variable=self.save_history_var,
            command=self._toggle_save_history,
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(frame, text="Rótulo do ciclo (ex: 1º Semestre 2025):").pack(anchor="w", pady=(0, 4))
        self.label_var = tk.StringVar(value=self._initial_label)
        self.label_entry = ttk.Entry(frame, textvariable=self.label_var, width=36)
        self.label_entry.pack(fill=tk.X, pady=4)

        sep = ttk.Separator(frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=8)

        self.keep_absences_var = tk.BooleanVar(value=False)
        self.keep_schedule_data_var = tk.BooleanVar(value=False)
        self.keep_event_history_var = tk.BooleanVar(value=False)
        self.keep_bonus_var = tk.BooleanVar(value=True)
        self.keep_draft_cards_var = tk.BooleanVar(value=False)
        self.keep_finalized_history_var = tk.BooleanVar(value=False)

        if self._info_title:
            ttk.Label(frame, text=self._info_title).pack(anchor="w")

        ttk.Label(
            frame,
            text=(
                "• O histórico só será salvo se a opção acima estiver marcada."
                if not self._show_retention_options
                else "• O sistema iniciará um novo ciclo com os dados escolhidos abaixo."
            ),
            foreground="gray",
        ).pack(anchor="w")
        if self._show_retention_options:
            ttk.Label(
                frame, text="• Dados não marcados serão limpos no novo ciclo.", foreground="gray"
            ).pack(anchor="w")

            keep_frame = ttk.LabelFrame(frame, text="Manter no novo ciclo", padding=8)
            keep_frame.pack(fill=tk.X, pady=8)

            ttk.Checkbutton(
                keep_frame,
                text="Faltas dos acólitos",
                variable=self.keep_absences_var,
            ).pack(anchor="w")
            ttk.Checkbutton(
                keep_frame,
                text="Contagem e histórico de escalas",
                variable=self.keep_schedule_data_var,
            ).pack(anchor="w")
            ttk.Checkbutton(
                keep_frame,
                text="Histórico de atividades",
                variable=self.keep_event_history_var,
            ).pack(anchor="w")
            ttk.Checkbutton(
                keep_frame,
                text="Bônus e movimentações de bônus",
                variable=self.keep_bonus_var,
            ).pack(anchor="w")
            ttk.Checkbutton(
                keep_frame,
                text="Cards rascunho de Convocação",
                variable=self.keep_draft_cards_var,
            ).pack(anchor="w")
            ttk.Checkbutton(
                keep_frame,
                text="Convocações/atividades finalizadas do ciclo atual",
                variable=self.keep_finalized_history_var,
            ).pack(anchor="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=self._action_text, command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

        self._toggle_save_history()

    def _toggle_save_history(self):
        state = tk.NORMAL if self.save_history_var.get() else tk.DISABLED
        self.label_entry.configure(state=state)

    def _ok(self):
        save_history = self.save_history_var.get()
        label = self.label_var.get().strip()
        if save_history and not label:
            messagebox.showwarning("Aviso", "Informe um rótulo para o ciclo.", parent=self)
            return
        self.result = {
            "save_history": save_history,
            "label": label,
            "keep_absences": self.keep_absences_var.get(),
            "keep_schedule_data": self.keep_schedule_data_var.get(),
            "keep_event_history": self.keep_event_history_var.get(),
            "keep_bonus": self.keep_bonus_var.get(),
            "keep_draft_cards": self.keep_draft_cards_var.get(),
            "keep_finalized_history": self.keep_finalized_history_var.get(),
        }
        self.destroy()


class BirthdaySettingsDialog(BaseDialog):
    """Diálogo para configurar envio automático de feliz aniversário via WhatsApp Web."""

    def __init__(self, parent, current_settings: dict):
        self._settings = current_settings.copy()
        super().__init__(parent, "Configurações de Aniversários")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Configurações de Aniversário Automático",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            frame,
            text='Ao ativar, o sistema pode enviar automaticamente uma mensagem\n'
                 'de "feliz aniversário" em um grupo do WhatsApp Web.',
            foreground="gray",
        ).pack(anchor="w", pady=(0, 8))

        self.enabled_var = tk.BooleanVar(value=self._settings.get("enabled", False))
        self._enabled_check = ttk.Checkbutton(
            frame,
            text="Ativar envio automático de feliz aniversário (temporariamente desativado)",
            variable=self.enabled_var,
            state=tk.DISABLED,
        )
        self._enabled_check.pack(anchor="w", pady=4)

        # Keep auto-send off while this feature is temporarily disabled.
        self.enabled_var.set(False)

        sep = ttk.Separator(frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=8)

        ttk.Label(frame, text="Nome do grupo no WhatsApp Web:").pack(anchor="w", pady=(4, 0))
        self.group_var = tk.StringVar(value=self._settings.get("whatsapp_group", ""))
        ttk.Entry(frame, textvariable=self.group_var, width=40).pack(fill=tk.X, pady=4)

        ttk.Label(frame, text="Mensagem de aniversário:").pack(anchor="w", pady=(4, 0))
        ttk.Label(
            frame,
            text="Use {nome} para inserir o nome do acólito.",
            foreground="gray",
        ).pack(anchor="w")
        self.message_text = tk.Text(frame, width=40, height=4, font=("TkDefaultFont", 10))
        self.message_text.pack(fill=tk.X, pady=4)
        self.message_text.insert(
            "1.0",
            self._settings.get("message_template", "Feliz aniversário, {nome}! 🎂🎉"),
        )

        ttk.Label(frame, text="Horário de envio (HH:MM):").pack(anchor="w", pady=(4, 0))
        self.time_var = tk.StringVar(value=self._settings.get("send_time", "08:00"))
        ttk.Entry(frame, textvariable=self.time_var, width=10).pack(anchor="w", pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Salvar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        send_time = self.time_var.get().strip()
        if send_time:
            try:
                parts = send_time.split(":")
                h, m = int(parts[0]), int(parts[1])
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except (ValueError, IndexError):
                messagebox.showwarning(
                    "Aviso", "Horário inválido. Use o formato HH:MM.", parent=self
                )
                return

        self.result = {
            "enabled": False,
            "whatsapp_group": self.group_var.get().strip(),
            "message_template": self.message_text.get("1.0", tk.END).strip(),
            "send_time": send_time,
        }
        self.destroy()


class BirthdayWeekDialog(BaseDialog):
    """Diálogo com aniversariantes da semana e opção de não exibir novamente por acólito."""

    def __init__(self, parent, birthday_items: list):
        self._birthday_items = birthday_items
        self._mute_vars = []
        super().__init__(parent, "Aniversários da Semana")
        self._build()
        self._center()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Aniversariantes desta semana:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        for item in self._birthday_items:
            item_frame = ttk.Frame(frame)
            item_frame.pack(fill=tk.X, pady=2)

            ttk.Label(item_frame, text=item.get("label", "")).pack(anchor="w")

            mute_var = tk.BooleanVar(value=False)
            self._mute_vars.append((item.get("id", ""), mute_var))
            ttk.Checkbutton(
                item_frame,
                text="Não mostrar novamente este aniversário",
                variable=mute_var,
            ).pack(anchor="w", padx=18)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(12, 0))
        ttk.Button(btn_frame, text="Fechar", command=self._ok).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        self.result = [acolyte_id for acolyte_id, var in self._mute_vars if acolyte_id and var.get()]
        self.destroy()
