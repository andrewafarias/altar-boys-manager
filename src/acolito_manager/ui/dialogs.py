"""Diálogos modais da aplicação."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox

from ..models import BonusMovement, StandardSlot, ScheduleSlot, Unavailability
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

        ttk.Label(frame, text="Nome da atividade:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data (DD/MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar()
        DateEntryFrame(frame, textvariable=self.date_var, width=8, date_format="DD/MM").grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
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
            messagebox.showwarning("Aviso", "Informe a data da atividade.", parent=self)
            return
        self.result = (name, date, time)
        self.destroy()


class AddEscalaGeralDialog(BaseDialog):
    """Diálogo para adicionar uma escala geral."""

    _last_include_as_activity: bool = True

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Escala Geral")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nome da escala geral:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=8, pady=4
        )

        ttk.Label(frame, text="Data (DD/MM):").grid(row=1, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar()
        DateEntryFrame(frame, textvariable=self.date_var, width=8, date_format="DD/MM").grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(frame, text="Horário (opcional, HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        TimeEntryFrame(frame, textvariable=self.time_var, width=10).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        self.include_as_activity_var = tk.BooleanVar(
            value=AddEscalaGeralDialog._last_include_as_activity
        )
        ttk.Checkbutton(
            frame, text="Incluir como atividade", variable=self.include_as_activity_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        self.include_as_schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, text="Incluir como escala", variable=self.include_as_schedule_var
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        name = self.name_var.get().strip()
        date = normalize_date(self.date_var.get().strip())
        time = self.time_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Informe o nome da escala geral.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data da escala geral.", parent=self)
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
        AddEscalaGeralDialog._last_include_as_activity = include_activity
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
    """Diálogo para gerenciar horários padrão."""

    def __init__(self, parent, app):
        self.app = app
        super().__init__(parent, "Gerenciar Horários Padrão")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Horários padrão são adicionados automaticamente à escala.",
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

        add_frame = ttk.LabelFrame(frame, text="Adicionar Horário Padrão", padding=8)
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

        ttk.Button(add_frame, text="➕ Adicionar", command=self._add_slot).grid(
            row=3, column=0, columnspan=2, pady=6
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="🗑️ Remover Selecionado", command=self._remove_slot).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(
            btn_row, text="📋 Adicionar à Escala Atual", command=self._add_to_schedule
        ).pack(side=tk.LEFT, padx=4)
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
            slot = ScheduleSlot(
                id=str(uuid.uuid4()), date=auto_date, day=ss.day,
                time=ss.time, description=ss.description,
            )
            self.app.schedule_slots.append(slot)
        self.app.schedule_tab.load_slots_from_data()
        self.app.save()
        messagebox.showinfo(
            "Concluído",
            f"{len(self.app.standard_slots)} horário(s) padrão adicionado(s) à escala.\n"
            "Datas preenchidas automaticamente.",
            parent=self,
        )

    def _ok(self):
        pass


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


class GeneralEventUnavailabilityDialog(BaseDialog):
    """Lista acólitos com conflito de indisponibilidade para uma escala geral."""

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
    """Edita quais acólitos serão excluídos de uma escala geral."""

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
        super().__init__(parent, "Editar Excluídos - Escala Geral")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Marque os acólitos que devem ficar excluídos desta escala geral:",
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


class CloseCicloDialog(BaseDialog):
    """Diálogo para fechar o ciclo atual."""

    def __init__(self, parent, initial_label: str = ""):
        self._initial_label = initial_label
        super().__init__(parent, "Fechar Ciclo")
        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Rótulo do ciclo (ex: 1º Semestre 2025):").pack(anchor="w", pady=(0, 4))
        self.label_var = tk.StringVar(value=self._initial_label)
        ttk.Entry(frame, textvariable=self.label_var, width=36).pack(fill=tk.X, pady=4)

        sep = ttk.Separator(frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=8)

        ttk.Label(frame, text="Ao fechar o ciclo:").pack(anchor="w")
        ttk.Label(
            frame, text="• As faltas de todos os acólitos serão resetadas.", foreground="gray"
        ).pack(anchor="w")
        ttk.Label(
            frame, text="• As escalas e atividades serão resetadas.", foreground="gray"
        ).pack(anchor="w")
        ttk.Label(
            frame, text="• O estado atual será salvo no histórico de ciclos.", foreground="gray"
        ).pack(anchor="w")

        self.reset_bonus_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Também resetar bônus de todos os acólitos",
            variable=self.reset_bonus_var
        ).pack(anchor="w", pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Fechar Ciclo", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        label = self.label_var.get().strip()
        if not label:
            messagebox.showwarning("Aviso", "Informe um rótulo para o ciclo.", parent=self)
            return
        self.result = (label, self.reset_bonus_var.get())
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
        ttk.Checkbutton(
            frame,
            text="Ativar envio automático de feliz aniversário",
            variable=self.enabled_var,
        ).pack(anchor="w", pady=4)

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
            "enabled": self.enabled_var.get(),
            "whatsapp_group": self.group_var.get().strip(),
            "message_template": self.message_text.get("1.0", tk.END).strip(),
            "send_time": send_time,
        }
        self.destroy()
