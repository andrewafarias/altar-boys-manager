"""Aplicação principal de gerenciamento de escala de acólitos."""

import os
import sys
import uuid
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
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
    """Detecta o dia da semana a partir de uma data no formato DD/MM."""
    try:
        parts = date_str.strip().split("/")
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            year = datetime.now().year
            dt = datetime(year, month, day)
            return WEEKDAYS_PT[dt.weekday()]
    except (ValueError, IndexError):
        pass
    return ""


def today_str() -> str:
    """Retorna a data de hoje no formato DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")


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
        ttk.Entry(frame, textvariable=self.date_var, width=20).grid(row=0, column=1, padx=8, pady=4)

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
        ttk.Entry(frame, textvariable=self.start_var, width=20).grid(row=1, column=1, padx=8, pady=4)

        ttk.Label(frame, text="Duração:").grid(row=2, column=0, sticky="w", pady=4)
        self.duration_var = tk.StringVar()
        e = ttk.Entry(frame, textvariable=self.duration_var, width=20)
        e.grid(row=2, column=1, padx=8, pady=4)
        e.insert(0, "ex: 2 semanas")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Confirmar", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _ok(self):
        reason = self.reason_var.get().strip()
        start = self.start_var.get().strip()
        duration = self.duration_var.get().strip()
        if not reason:
            messagebox.showwarning("Aviso", "Informe o motivo.", parent=self)
            return
        self.result = (reason, start, duration)
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
        self.amount_var = tk.IntVar(value=1)
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
            amount = int(self.amount_var.get())
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
        ttk.Entry(frame, textvariable=self.date_var, width=15).grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frame, text="Horário (opcional, HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.time_var, width=10).grid(row=2, column=1, padx=8, pady=4, sticky="w")

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


# ---------------------------------------------------------------------------
# Painel de slot de escala (widget reutilizável)
# ---------------------------------------------------------------------------

class ScheduleSlotCard(ttk.LabelFrame):
    """
    Widget que representa um horário de escala.
    Exibe campos de data, horário, descrição e lista de acólitos atribuídos.
    """

    def __init__(self, parent, slot: ScheduleSlot, app, **kwargs):
        super().__init__(parent, text=f"Horário #{slot.id[:6]}", padding=6, **kwargs)
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
        ttk.Entry(row1, textvariable=self.date_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Hora:").pack(side=tk.LEFT, padx=(6, 0))
        self.time_var = tk.StringVar(value=self.slot.time)
        self.time_var.trace_add("write", self._on_field_change)
        ttk.Entry(row1, textvariable=self.time_var, width=6).pack(side=tk.LEFT, padx=2)

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
            text="➕ Adicionar Acólito Selecionado",
            command=self._add_selected_acolyte,
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

    def _add_selected_acolyte(self):
        acolyte = self.app.get_selected_acolyte_for_schedule()
        if acolyte is None:
            messagebox.showinfo("Aviso", "Selecione um acólito na lista à direita.", parent=self)
            return
        if acolyte.id in self.slot.acolyte_ids:
            messagebox.showinfo("Aviso", f"{acolyte.name} já está neste horário.", parent=self)
            return
        self.slot.acolyte_ids.append(acolyte.id)
        self._refresh_acolytes()
        self.app.save()

    def _remove_acolyte(self, acolyte_id: str):
        if acolyte_id in self.slot.acolyte_ids:
            self.slot.acolyte_ids.remove(acolyte_id)
        self._refresh_acolytes()
        self.app.save()

    def _refresh_acolytes(self):
        for widget in self.acolyte_frame.winfo_children():
            widget.destroy()
        self._acolyte_labels.clear()

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
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

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
        paned.add(right, minsize=200)

        ttk.Label(right, text="Acólitos (por escalas ↑)", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(right)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.acolyte_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("TkDefaultFont", 9),
            activestyle="dotbox",
        )
        self.acolyte_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.acolyte_listbox.yview)

    def refresh_acolyte_list(self):
        """Atualiza a lista de acólitos ordenada por vezes escalado."""
        self.acolyte_listbox.delete(0, tk.END)
        sorted_acolytes = sorted(self.app.acolytes, key=lambda a: a.times_scheduled)
        for ac in sorted_acolytes:
            suffix = " (suspenso)" if ac.is_suspended else ""
            self.acolyte_listbox.insert(tk.END, f"{ac.name}{suffix} ({ac.times_scheduled} escalas)")

        # Colorir acólitos suspensos de vermelho
        sorted_acolytes_list = list(sorted_acolytes)
        for i, ac in enumerate(sorted_acolytes_list):
            if ac.is_suspended:
                self.acolyte_listbox.itemconfig(i, foreground="red")

    def get_selected_acolyte(self) -> Optional[Acolyte]:
        """Retorna o acólito selecionado na lista."""
        sel = self.acolyte_listbox.curselection()
        if not sel:
            return None
        sorted_acolytes = sorted(self.app.acolytes, key=lambda a: a.times_scheduled)
        idx = sel[0]
        if idx < len(sorted_acolytes):
            return sorted_acolytes[idx]
        return None

    def _add_slot(self):
        slot = ScheduleSlot(id=str(uuid.uuid4()), date="", day="", time="")
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

        lines = ["ESCALA DA SEMANA\n"]
        for slot in self.app.schedule_slots:
            header = f"{slot.day}, {slot.date} - {slot.time}:"
            lines.append(header)
            if slot.description:
                lines.append(slot.description)
            names = []
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    names.append(ac.name)
            lines.append(names_list_to_text(names))
            lines.append("")

        text = "\n".join(lines).strip()

        # Atualiza contadores e histórico de cada acólito
        for slot in self.app.schedule_slots:
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

        # Limpa os slots após finalizar
        self.app.schedule_slots.clear()
        self._slot_cards.clear()
        for widget in self.slots_frame.winfo_children():
            widget.destroy()

        self.app.save()
        self.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()

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

        # Botão finalizar eventos
        ttk.Button(
            left,
            text="✅ Finalizar Eventos",
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
        ttk.Entry(fields, textvariable=self.ev_date_var, width=12).grid(row=1, column=1, padx=6, pady=4, sticky="w")

        ttk.Label(fields, text="Horário:").grid(row=2, column=0, sticky="w", pady=4)
        self.ev_time_var = tk.StringVar()
        ttk.Entry(fields, textvariable=self.ev_time_var, width=10).grid(row=2, column=1, padx=6, pady=4, sticky="w")

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
        self.ev_name_var.set(ev.name)
        self.ev_date_var.set(ev.date)
        self.ev_time_var.set(ev.time)
        self._rebuild_participants()

    def _rebuild_participants(self):
        for widget in self.participants_inner.winfo_children():
            widget.destroy()
        self._acolyte_vars.clear()

        ev = self._current_event
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
        count = 0
        for ev in self.app.general_events:
            for ac in self.app.acolytes:
                if ac.id not in ev.excluded_acolyte_ids:
                    entry = EventHistoryEntry(
                        event_id=ev.id,
                        name=ev.name,
                        date=ev.date,
                        time=ev.time,
                    )
                    ac.event_history.append(entry)
                    count += 1
        self.app.save()
        messagebox.showinfo("Concluído", f"Eventos finalizados! {count} registros adicionados.")


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
        self.bonus_direct_var = tk.IntVar(value=0)
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
        self._tree_events = self._make_tree(
            self._tab_events, ("Nome do Evento", "Data", "Horário"), (220, 80, 80)
        )
        self._tree_absences = self._make_tree(
            self._tab_absences, ("Data", "Descrição"), (100, 300)
        )
        self._tree_suspensions = self._make_tree(
            self._tab_suspensions, ("Motivo", "Início", "Duração", "Ativa"), (200, 90, 100, 60)
        )
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
                self.acolyte_listbox.itemconfig(i, foreground="red")

        # Restaura seleção
        if sel_id:
            for i, ac in enumerate(sorted_acs):
                if ac.id == sel_id:
                    self.acolyte_listbox.selection_set(i)
                    break

    def _on_acolyte_select(self, event=None):
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
        self._show_detail()
        susp_text = " 🔴 SUSPENSO" if ac.is_suspended else ""
        self.name_label.config(text=f"{ac.name}{susp_text}")
        self.summary_label.config(
            text=(
                f"Escalas: {ac.times_scheduled}  |  Faltas: {ac.absence_count}  |  "
                f"Suspensões: {ac.suspension_count}  |  Bônus: {ac.bonus_count}"
            )
        )
        self.bonus_direct_var.set(ac.bonus_count)

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
            (s.reason, s.start_date, s.duration, "Sim" if s.is_active else "Não")
            for s in ac.suspensions
        ])
        self._refresh_tree(self._tree_bonus, [
            ("Ganho" if b.type == "earn" else "Usado", str(b.amount), b.description or "-", b.date)
            for b in ac.bonus_movements
        ])

    def _refresh_tree(self, tree: ttk.Treeview, rows: list):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)

    def _add_acolyte(self):
        name = simpledialog.askstring("Novo Acólito", "Nome do acólito:", parent=self.app.root)
        if not name:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning("Aviso", "O nome não pode estar vazio.")
            return
        # Avisa se já existe, mas permite
        existing = [a for a in self.app.acolytes if a.name.lower() == name.lower()]
        if existing:
            if not messagebox.askyesno(
                "Nome duplicado",
                f"Já existe um acólito chamado '{name}'. Deseja adicionar mesmo assim?",
            ):
                return
        ac = Acolyte(id=str(uuid.uuid4()), name=name)
        self.app.acolytes.append(ac)
        self.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.save()

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
            reason, start, duration = dlg.result
            susp = Suspension(
                id=str(uuid.uuid4()),
                reason=reason,
                start_date=start,
                duration=duration,
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
        if not ac.is_suspended:
            messagebox.showinfo("Aviso", f"{ac.name} não está suspenso.")
            return
        active = ac.active_suspension
        if active:
            active.is_active = False
        ac.is_suspended = False
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
            new_val = int(self.bonus_direct_var.get())
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
                os.startfile(path)
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Aplicação principal
# ---------------------------------------------------------------------------

class App:
    def __init__(self):
        self.acolytes: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []

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

        self.notebook.add(self.schedule_tab, text="📅 Criar Escala")
        self.notebook.add(self.events_tab, text="🎉 Eventos Gerais")
        self.notebook.add(self.acolytes_tab, text="👥 Acólitos")

    def _load_data(self):
        self.acolytes, self.schedule_slots, self.general_events = data_manager.load_data()
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data()
        self.events_tab.refresh_list()
        self.acolytes_tab.refresh_list()

    def save(self):
        data_manager.save_data(self.acolytes, self.schedule_slots, self.general_events)

    def find_acolyte(self, acolyte_id: str) -> Optional[Acolyte]:
        for ac in self.acolytes:
            if ac.id == acolyte_id:
                return ac
        return None

    def get_selected_acolyte_for_schedule(self) -> Optional[Acolyte]:
        """Retorna o acólito selecionado na aba de escalas."""
        return self.schedule_tab.get_selected_acolyte()

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
