"""Diálogos modais da aplicação."""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox

from ..models import BonusMovement, StandardSlot
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
        self._center()
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


class AddScheduleEntryDialog(BaseDialog):
    """Diálogo para adicionar uma entrada no histórico de escalas."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Entrada de Escala")
        self._build()
        self._center()
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
        self._center()
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
        self._center()
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
        self._center()
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
        self._center()
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
        self._center()
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
        messagebox.showinfo(
            "Copiado", "Texto copiado para a área de transferência!", parent=self
        )


class AddEventDialog(BaseDialog):
    """Diálogo para adicionar uma atividade."""

    def __init__(self, parent):
        super().__init__(parent, "Adicionar Atividade Geral")
        self._build()
        self._center()
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

        self.include_as_activity_var = tk.BooleanVar(value=True)
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
            messagebox.showwarning("Aviso", "Informe o nome da atividade.", parent=self)
            return
        if not date:
            messagebox.showwarning("Aviso", "Informe a data da atividade.", parent=self)
            return
        self.result = (
            name,
            date,
            time,
            self.include_as_activity_var.get(),
            self.include_as_schedule_var.get(),
        )
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
        self._center()
        self.wait_window()

    def _build(self):
        from models import ScheduleSlot

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
        from models import ScheduleSlot

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
