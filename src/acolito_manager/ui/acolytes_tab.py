"""Aba de gerenciamento de acólitos."""

import sys
import uuid
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from datetime import datetime

from ..report_generator import generate_report
from ..models import (
    Acolyte,
    Absence,
    Suspension,
    BonusMovement,
    ScheduleHistoryEntry,
    ActivityHistoryEntry,
    Unavailability,
    TemporaryUnavailability,
)
from ..utils import today_str, is_currently_suspended
from .dialogs import (
    AddAbsenceDialog,
    EditAbsenceDialog,
    AddScheduleEntryDialog,
    AddEventEntryDialog,
    SuspendDialog,
    SelectSuspensionsDialog,
    EditSuspensionDialog,
    BonusDialog,
    EditBonusMovementDialog,
    AddMultipleAcolytesDialog,
    AddUnavailabilityDialog,
    AddTemporaryUnavailabilityDialog,
    EditUnavailabilityDialog,
    CloseCicloDialog,
)


class AcolytesTab(ttk.Frame):
    """Aba de gerenciamento de acólitos."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._current_acolyte: Optional[Acolyte] = None
        self._overview_frame = None
        self._notes_save_job = None
        self._loading_notes = False
        self._overview_shown_once = False
        self._build()

    # --------------------------------------------------------------------- #
    #  UI Construction
    # --------------------------------------------------------------------- #

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
            exportselection=False,
        )
        self.acolyte_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.acolyte_listbox.yview)
        self.acolyte_listbox.bind("<<ListboxSelect>>", self._on_acolyte_select)

        # Botões do rodapé
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
        cycle_name_frame = ttk.LabelFrame(left, text="Ciclo Atual", padding=4)
        cycle_name_frame.pack(fill=tk.X, pady=2)
        self.current_cycle_name_var = tk.StringVar(value=self.app.current_cycle_name)
        self.current_cycle_name_entry = ttk.Entry(
            cycle_name_frame,
            textvariable=self.current_cycle_name_var,
        )
        self.current_cycle_name_entry.pack(fill=tk.X)
        self.current_cycle_name_entry.bind("<FocusOut>", lambda _e: self._save_current_cycle_name())
        self.current_cycle_name_entry.bind("<Return>", lambda _e: self._save_current_cycle_name())
        ttk.Button(left, text="📊 Visão Geral", command=self._show_overview_table).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="📕 Fechar Ciclo", command=self._close_cycle).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="📄 Gerar Relatório PDF", command=self._generate_report).pack(fill=tk.X, pady=2)

        # --- Painel direito ---
        self.right = ttk.Frame(paned, padding=6)
        paned.add(self.right, minsize=480)
        self._build_detail_panel()

        # Show Visão Geral automatically the first time this tab becomes visible.
        self.bind("<Visibility>", self._on_first_visit)

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

        # Data de nascimento
        bd_frame = ttk.Frame(self.detail_frame)
        bd_frame.pack(anchor="w", pady=2)
        ttk.Label(bd_frame, text="Nascimento:").pack(side=tk.LEFT)
        self.birthdate_var = tk.StringVar()
        ttk.Entry(
            bd_frame, textvariable=self.birthdate_var, width=12
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(bd_frame, text="Salvar", command=self._save_birthdate, width=6).pack(
            side=tk.LEFT, padx=2
        )
        self.birthdate_display = ttk.Label(bd_frame, text="", foreground="#555")
        self.birthdate_display.pack(side=tk.LEFT, padx=6)

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
        self.bonus_spin = tk.Spinbox(
            bonus_frame,
            from_=0,
            to=9999,
            textvariable=self.bonus_direct_var,
            width=6,
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
        self._tab_unavailabilities = ttk.Frame(self.detail_notebook)
        self._tab_internal_notes = ttk.Frame(self.detail_notebook)

        self.detail_notebook.add(self._tab_schedule, text="Histórico de Escalas")
        self.detail_notebook.add(self._tab_events, text="Atividades")
        self.detail_notebook.add(self._tab_absences, text="Faltas")
        self.detail_notebook.add(self._tab_suspensions, text="Suspensões")
        self.detail_notebook.add(self._tab_bonus, text="Movimentação de Bônus")
        self.detail_notebook.add(self._tab_unavailabilities, text="Indisponibilidades")
        self.detail_notebook.add(self._tab_internal_notes, text="Notas Internas")

        notes_container = ttk.Frame(self._tab_internal_notes, padding=6)
        notes_container.pack(fill=tk.BOTH, expand=True)
        self.internal_notes_text = tk.Text(
            notes_container,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=100,
        )
        self.internal_notes_text.pack(fill=tk.BOTH, expand=True)
        self.internal_notes_text.bind("<KeyRelease>", self._on_internal_notes_change)
        self.internal_notes_text.bind("<FocusOut>", self._on_internal_notes_focus_out)

        # Atalhos de edição para facilitar o uso das notas.
        self.internal_notes_text.bind("<Control-z>", self._notes_undo)
        self.internal_notes_text.bind("<Control-Z>", self._notes_undo)
        self.internal_notes_text.bind("<Control-Shift-z>", self._notes_redo)
        self.internal_notes_text.bind("<Control-Shift-Z>", self._notes_redo)
        self.internal_notes_text.bind("<Control-y>", self._notes_redo)
        self.internal_notes_text.bind("<Control-Y>", self._notes_redo)
        self.internal_notes_text.bind("<Control-a>", self._notes_select_all)
        self.internal_notes_text.bind("<Control-A>", self._notes_select_all)
        self.internal_notes_text.bind("<Control-c>", self._notes_copy)
        self.internal_notes_text.bind("<Control-C>", self._notes_copy)
        self.internal_notes_text.bind("<Control-v>", self._notes_paste)
        self.internal_notes_text.bind("<Control-V>", self._notes_paste)
        self.internal_notes_text.bind("<Control-x>", self._notes_cut)
        self.internal_notes_text.bind("<Control-X>", self._notes_cut)

        # Criação das tabelas
        self._tree_schedule = self._make_tree(
            self._tab_schedule, ("Data", "Dia", "Horário", "Descrição", "Faltou"), (80, 120, 70, 180, 70)
        )
        sched_btn_frame = ttk.Frame(self._tab_schedule)
        sched_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(sched_btn_frame, text="➕ Adicionar Entrada", command=self._add_schedule_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(sched_btn_frame, text="🗑️ Excluir Entrada", command=self._delete_schedule_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(sched_btn_frame, text="⚠️ Marcar/Desmarcar Faltou", command=self._toggle_schedule_missed).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            sched_btn_frame,
            text="🏷️ Marcar/Desmarcar Falta simbólica",
            command=self._toggle_schedule_symbolic_missed,
        ).pack(side=tk.LEFT, padx=2)

        self._tree_events = self._make_tree(
            self._tab_events, ("Nome da Atividade", "Data", "Horário", "Faltou"), (210, 80, 80, 70)
        )
        event_btn_frame = ttk.Frame(self._tab_events)
        event_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(event_btn_frame, text="➕ Adicionar Entrada", command=self._add_event_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(event_btn_frame, text="🗑️ Excluir Entrada", command=self._delete_event_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(event_btn_frame, text="⚠️ Marcar/Desmarcar Faltou", command=self._toggle_event_missed).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            event_btn_frame,
            text="🏷️ Marcar/Desmarcar Falta simbólica",
            command=self._toggle_event_symbolic_missed,
        ).pack(side=tk.LEFT, padx=2)

        self._tree_absences = self._make_tree(
            self._tab_absences, ("Data", "Descrição", "Vinculada", "Simbólica"), (100, 260, 110, 90)
        )
        abs_btn_frame = ttk.Frame(self._tab_absences)
        abs_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(abs_btn_frame, text="✏️ Editar Falta", command=self._edit_absence).pack(side=tk.LEFT, padx=2)
        ttk.Button(abs_btn_frame, text="🗑️ Excluir Falta", command=self._delete_absence).pack(side=tk.LEFT, padx=2)
        self._tree_suspensions = self._make_tree(
            self._tab_suspensions, ("Motivo", "Início", "Fim", "Ativa"), (180, 100, 100, 60)
        )
        susp_btn_frame = ttk.Frame(self._tab_suspensions)
        susp_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(susp_btn_frame, text="✏️ Editar Suspensão", command=self._edit_suspension).pack(side=tk.LEFT, padx=2)
        ttk.Button(susp_btn_frame, text="🗑️ Excluir Suspensão", command=self._delete_suspension).pack(side=tk.LEFT, padx=2)

        self._tree_bonus = self._make_tree(
            self._tab_bonus, ("Tipo", "Quantidade", "Descrição", "Data"), (70, 80, 220, 90)
        )
        bonus_btn_frame = ttk.Frame(self._tab_bonus)
        bonus_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(
            bonus_btn_frame,
            text="✏️ Editar Movimentação",
            command=self._edit_bonus_movement,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            bonus_btn_frame,
            text="🗑️ Excluir Movimentação",
            command=self._delete_bonus_movement,
        ).pack(side=tk.LEFT, padx=2)

        # Indisponibilidades tab
        self._unav_items: list = []  # [("regular"|"temporary", obj), ...]
        self._tree_unavailabilities = self._make_tree(
            self._tab_unavailabilities,
            ("Tipo", "Dia", "Hora Início", "Hora Fim"),
            (90, 175, 90, 90)
        )
        unav_btn_frame = ttk.Frame(self._tab_unavailabilities)
        unav_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(unav_btn_frame, text="➕ Semanal", command=self._add_unavailability).pack(side=tk.LEFT, padx=2)
        ttk.Button(unav_btn_frame, text="➕ Temporária", command=self._add_temp_unavailability).pack(side=tk.LEFT, padx=2)
        ttk.Button(unav_btn_frame, text="✏️ Editar", command=self._edit_unavailability).pack(side=tk.LEFT, padx=2)
        ttk.Button(unav_btn_frame, text="🗑️ Excluir", command=self._delete_unavailability).pack(side=tk.LEFT, padx=2)

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

    # --------------------------------------------------------------------- #
    #  List / Selection
    # --------------------------------------------------------------------- #

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
            self.acolyte_listbox.insert(
                tk.END, f"{ac.name}{suffix}"
            )

        for i, ac in enumerate(sorted_acs):
            if ac.is_suspended:
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
                    self.acolyte_listbox.itemconfig(i, foreground="#B8860B")
                else:
                    self.acolyte_listbox.itemconfig(i, foreground="red")

        # Restaura seleção
        if sel_id:
            for i, ac in enumerate(sorted_acs):
                if ac.id == sel_id:
                    self.acolyte_listbox.selection_set(i)
                    break

    def _refresh_calendar_views(self):
        cal_tab = getattr(self.app, "calendar_tab", None)
        if cal_tab is None:
            return
        cal_tab.refresh_open_dialogs()

    def _on_acolyte_select(self, event=None):
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

    def _on_first_visit(self, event=None):
        """Show Visão Geral automatically the first time the tab becomes visible."""
        if self._overview_shown_once:
            return
        self._overview_shown_once = True
        self.unbind("<Visibility>")
        if self.app.acolytes:
            self._show_overview_table()

    def sync_current_cycle_name(self):
        if hasattr(self, "current_cycle_name_var"):
            self.current_cycle_name_var.set(self.app.current_cycle_name)

    def _save_current_cycle_name(self):
        new_value = self.current_cycle_name_var.get().strip()
        if new_value == self.app.current_cycle_name:
            return
        self.app.current_cycle_name = new_value
        self.app.save()

    # --------------------------------------------------------------------- #
    #  Detail Display
    # --------------------------------------------------------------------- #

    def _show_acolyte_detail(self):
        ac = self._current_acolyte
        if not ac:
            return
        self._show_detail()

        self._check_suspension_expiry(ac)

        susp_text = ""
        if ac.is_suspended:
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
        else:
            has_future_suspension = False
            for s in ac.suspensions:
                if s.is_active and s.start_date:
                    try:
                        start_dt = datetime.strptime(s.start_date, "%d/%m/%Y")
                        if start_dt.date() > datetime.now().date():
                            has_future_suspension = True
                            break
                    except ValueError:
                        pass
            if has_future_suspension:
                susp_text = " 🟠 SERÁ SUSPENDIDO"

        self.name_label.config(text=f"{ac.name}{susp_text}")
        activity_count = len(ac.event_history)
        self.summary_label.config(
            text=(
                f"Escalas: {ac.times_scheduled}  |  Atividades: {activity_count}  |  "
                f"Faltas: {ac.absence_count}  |  "
                f"Suspensões: {ac.suspension_count}  |  Bônus: {ac.bonus_count}"
            )
        )
        self._loading_notes = True
        self.internal_notes_text.delete("1.0", tk.END)
        self.internal_notes_text.insert("1.0", ac.internal_notes or "")
        self._loading_notes = False
        self.birthdate_var.set(ac.birthdate if ac.birthdate else "")
        if ac.birthdate:
            try:
                bd = datetime.strptime(ac.birthdate, "%d/%m/%Y")
                today = datetime.now()
                age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                self.birthdate_display.config(text=f"({age} anos)")
            except ValueError:
                self.birthdate_display.config(text="")
        else:
            self.birthdate_display.config(text="")
        # Temporarily disconnect spinbox command
        old_command = self.bonus_spin.config('command')[-1]
        self.bonus_spin.config(command='')
        self.bonus_direct_var.set(str(ac.bonus_count))
        self.bonus_spin.config(command=old_command if old_command else self._set_bonus_direct)

        # Atualiza as tabelas
        self._refresh_tree(self._tree_schedule, [
            (
                e.date,
                e.day,
                e.time,
                e.description or "-",
                self._format_missed_display(ac, "schedule", e.schedule_id, e.missed),
            )
            for e in ac.schedule_history
        ])
        self._refresh_tree(self._tree_events, [
            (
                e.name,
                e.date,
                e.time or "-",
                self._format_missed_display(ac, "event", e.event_id, e.missed),
            )
            for e in ac.event_history
        ])
        self._refresh_tree(self._tree_absences, [
                (
                    a.date,
                    a.description or "-",
                    "Sim" if a.linked_entry_type else "Não",
                    "Sim" if a.is_symbolic else "Não",
                )
                for a in ac.absences
            ])
        self._refresh_tree(self._tree_suspensions, [
            (s.reason, s.start_date, s.end_date or "-", "Sim" if s.is_active else "Não")
            for s in ac.suspensions
        ])
        # Highlight expired and future suspensions
        for i, s in enumerate(ac.suspensions):
            if s.is_active:
                items = self._tree_suspensions.get_children()
                if i < len(items):
                    if s.end_date:
                        try:
                            end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                            if end_dt.date() <= datetime.now().date():
                                self._tree_suspensions.tag_configure("expired", background="#FFFF99")
                                self._tree_suspensions.item(items[i], tags=("expired",))
                                continue
                        except ValueError:
                            pass

                    if s.start_date:
                        try:
                            start_dt = datetime.strptime(s.start_date, "%d/%m/%Y")
                            if start_dt.date() > datetime.now().date():
                                self._tree_suspensions.tag_configure("future", background="#FFD699")
                                self._tree_suspensions.item(items[i], tags=("future",))
                        except ValueError:
                            pass

        self._refresh_tree(self._tree_bonus, [
            ("Ganho" if b.type == "earn" else "Usado", str(b.amount), b.description or "-", b.date)
            for b in ac.bonus_movements
        ])
        self._unav_items = [
            ("regular", u) for u in getattr(ac, 'unavailabilities', [])
        ] + [
            ("temporary", t) for t in getattr(ac, 'temporary_unavailabilities', [])
        ]
        unav_rows = []
        for kind, u in self._unav_items:
            if kind == "regular":
                st = u.start_time if u.start_time else "Dia todo"
                et = u.end_time if u.end_time else "Dia todo"
                unav_rows.append(("Semanal", u.day, st, et))
            else:
                sd = self._to_short_date(u.start_date)
                ed = self._to_short_date(u.end_date)
                day_label = f"{sd} – {ed}"
                st = u.start_time if u.start_time else "Dia todo"
                et = u.end_time if u.end_time else "Dia todo"
                unav_rows.append(("Temporária", day_label, st, et))
        self._refresh_tree(self._tree_unavailabilities, unav_rows)

    def _refresh_tree(self, tree: ttk.Treeview, rows: list):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)

    def _to_short_date(self, date_str: str) -> str:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%d/%m/%y")
        except ValueError:
            return date_str or "-"

    def _find_linked_absence(self, ac: Acolyte, entry_type: str, entry_id: str) -> Optional[Absence]:
        for absence in ac.absences:
            if absence.linked_entry_type == entry_type and absence.linked_entry_id == entry_id:
                return absence
        return None

    def _format_missed_display(self, ac: Acolyte, entry_type: str, entry_id: str, missed: bool) -> str:
        if not missed:
            return "Não"
        linked_absence = self._find_linked_absence(ac, entry_type, entry_id)
        if linked_absence and linked_absence.is_symbolic:
            return "Sim (simbólica)"
        return "Sim"

    def _save_birthdate(self):
        ac = self._current_acolyte
        if not ac:
            return
        bd = self.birthdate_var.get().strip()
        if bd:
            try:
                datetime.strptime(bd, "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning(
                    "Aviso", "Data inválida. Use o formato DD/MM/AAAA.", parent=self.app.root
                )
                return
        ac.birthdate = bd
        self.app.save()
        self._show_acolyte_detail()

    def _clear_linked_missed_flag(self, ac: Acolyte, absence: Absence):
        if absence.linked_entry_type == "schedule":
            for entry in ac.schedule_history:
                if entry.schedule_id == absence.linked_entry_id:
                    entry.missed = False
                    return
        if absence.linked_entry_type == "event":
            for entry in ac.event_history:
                if entry.event_id == absence.linked_entry_id:
                    entry.missed = False
                    return

    def _build_linked_absence_description(self, entry_type: str, entry) -> str:
        label = "atividade" if entry_type == "event" else "escala"
        if entry_type == "event":
            detail = entry.name or "Sem descrição"
        else:
            detail = entry.description or "Sem descrição"
        date_short = self._to_short_date(entry.date)
        time_text = (entry.time or "").strip()
        suffix = f" {time_text}" if time_text else ""
        return f"Faltou {label}: {detail} {date_short}{suffix}"

    def _sync_linked_absence(self, ac: Acolyte, entry_type: str, entry, missed: bool):
        entry_id = entry.event_id if entry_type == "event" else entry.schedule_id
        existing = self._find_linked_absence(ac, entry_type, entry_id)
        if missed:
            description = self._build_linked_absence_description(entry_type, entry)
            if existing:
                existing.date = entry.date
                existing.description = description
            else:
                ac.absences.append(
                    Absence(
                        id=str(uuid.uuid4()),
                        date=entry.date,
                        description=description,
                        linked_entry_type=entry_type,
                        linked_entry_id=entry_id,
                    )
                )
        elif existing:
            ac.absences.remove(existing)

    def _check_suspension_expiry(self, ac):
        """Check if any suspension end_date has been reached."""
        changed = False
        for s in ac.suspensions:
            if s.is_active and s.end_date:
                try:
                    end_dt = datetime.strptime(s.end_date, "%d/%m/%Y")
                    if end_dt.date() <= datetime.now().date():
                        if self.app.auto_lift_suspensions_on_end_date:
                            s.is_active = False
                            changed = True
                except ValueError:
                    pass

        if changed:
            ac.is_suspended = is_currently_suspended(ac)
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

    # --------------------------------------------------------------------- #
    #  Add / Remove Acolytes
    # --------------------------------------------------------------------- #

    def _on_internal_notes_change(self, _event=None):
        if self._loading_notes:
            return
        if self._notes_save_job is not None:
            self.after_cancel(self._notes_save_job)
        self._notes_save_job = self.after(400, self._save_internal_notes)

    def _on_internal_notes_focus_out(self, _event=None):
        self._save_internal_notes()

    def _notes_undo(self, _event=None):
        try:
            self.internal_notes_text.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _notes_redo(self, _event=None):
        try:
            self.internal_notes_text.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def _notes_select_all(self, _event=None):
        self.internal_notes_text.tag_add(tk.SEL, "1.0", tk.END)
        self.internal_notes_text.mark_set(tk.INSERT, "1.0")
        self.internal_notes_text.see(tk.INSERT)
        return "break"

    def _notes_copy(self, _event=None):
        self.internal_notes_text.event_generate("<<Copy>>")
        return "break"

    def _notes_paste(self, _event=None):
        self.internal_notes_text.event_generate("<<Paste>>")
        return "break"

    def _notes_cut(self, _event=None):
        self.internal_notes_text.event_generate("<<Cut>>")
        return "break"

    def _save_internal_notes(self):
        if not self._current_acolyte:
            return
        if self._notes_save_job is not None:
            self.after_cancel(self._notes_save_job)
            self._notes_save_job = None
        notes = self.internal_notes_text.get("1.0", tk.END).rstrip()
        if self._current_acolyte.internal_notes == notes:
            return
        self._current_acolyte.internal_notes = notes
        self.app.save()

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
            existing = [a for a in self.app.acolytes if a.name.lower() == name.lower()]
            if existing:
                duplicates.append(name)
                continue
            ac = Acolyte(id=str(uuid.uuid4()), name=name)
            self.app.acolytes.append(ac)
            added_count += 1

        if added_count > 0:
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

        if added_count > 0 and duplicates:
            messagebox.showinfo(
                "Concluído",
                f"{added_count} acólito(s) adicionado(s) com sucesso.\n\n"
                f"Nomes duplicados ignorados: {', '.join(duplicates)}",
                parent=self.app.root,
            )
        elif added_count > 0:
            messagebox.showinfo(
                "Sucesso",
                f"{added_count} acólito(s) adicionado(s) com sucesso!",
                parent=self.app.root,
            )
        elif duplicates:
            messagebox.showwarning(
                "Aviso",
                f"Todos os nomes já existem no sistema:\n{', '.join(duplicates)}",
                parent=self.app.root,
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

    # --------------------------------------------------------------------- #
    #  Suspension
    # --------------------------------------------------------------------- #

    def _suspend(self):
        if not self._current_acolyte:
            return
        dlg = SuspendDialog(self.app.root)
        if dlg.result:
            reason, start, end_date = dlg.result
            susp = Suspension(
                id=str(uuid.uuid4()),
                reason=reason,
                start_date=start,
                end_date=end_date,
                is_active=True,
            )
            ac = self._current_acolyte
            ac.suspensions.append(susp)
            ac.is_suspended = is_currently_suspended(ac)
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
            ac.is_suspended = is_currently_suspended(ac)
            self._show_acolyte_detail()
            self.refresh_list()
            self.app.schedule_tab.refresh_acolyte_list()
            self.app.save()

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
            susp.is_active = dlg.result["is_active"]
            ac.is_suspended = is_currently_suspended(ac)
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
        ac.is_suspended = is_currently_suspended(ac)
        self._show_acolyte_detail()
        self.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.save()

    # --------------------------------------------------------------------- #
    #  Absences
    # --------------------------------------------------------------------- #

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
            self._refresh_calendar_views()

    def _edit_absence(self):
        if not self._current_acolyte:
            return
        sel = self._tree_absences.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma falta para editar.")
            return
        idx = self._tree_absences.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.absences):
            return
        absence = ac.absences[idx]
        dlg = EditAbsenceDialog(self.app.root, absence)
        if dlg.result:
            absence.date = dlg.result["date"]
            absence.description = dlg.result["description"]
            absence.is_symbolic = dlg.result["is_symbolic"]
            self._show_acolyte_detail()
            self.app.save()
            self._refresh_calendar_views()

    def _delete_absence(self):
        if not self._current_acolyte:
            return
        sel = self._tree_absences.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma falta para excluir.")
            return
        idx = self._tree_absences.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.absences):
            return
        absence = ac.absences[idx]
        if not messagebox.askyesno("Confirmar", f"Excluir falta de {absence.date}?"):
            return
        self._clear_linked_missed_flag(ac, absence)

        ac.absences.pop(idx)
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _toggle_symbolic_absence(self):
        if not self._current_acolyte:
            return
        sel = self._tree_absences.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma falta para editar.")
            return
        idx = self._tree_absences.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.absences):
            return
        absence = ac.absences[idx]
        absence.is_symbolic = not absence.is_symbolic
        status = "(não contada)" if absence.is_symbolic else "(contada)"
        messagebox.showinfo("Sucesso", f"Falta de {absence.date} agora é {status}")
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()
    # --------------------------------------------------------------------- #
    #  Bonus
    # --------------------------------------------------------------------- #

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
        activity_count = len(self._current_acolyte.event_history)
        self.summary_label.config(
            text=(
                f"Escalas: {self._current_acolyte.times_scheduled}  |  "
                f"Atividades: {activity_count}  |  "
                f"Faltas: {self._current_acolyte.absence_count}  |  "
                f"Suspensões: {self._current_acolyte.suspension_count}  |  "
                f"Bônus: {self._current_acolyte.bonus_count}"
            )
        )
        self.app.save()

    def _apply_bonus_impact(self, bonus_count: int, movement_type: str, amount: int) -> int:
        """Aplica o impacto de uma movimentação de bônus ao saldo informado."""
        if movement_type == "earn":
            return bonus_count + amount
        return bonus_count - amount

    def _edit_bonus_movement(self):
        """Edit the selected bonus movement."""
        if not self._current_acolyte:
            return
        sel = self._tree_bonus.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma movimentação de bônus para editar.")
            return

        idx = self._tree_bonus.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.bonus_movements):
            return

        movement = ac.bonus_movements[idx]
        dlg = EditBonusMovementDialog(self.app.root, movement)
        if not dlg.result:
            return

        updated = dlg.result
        base_bonus = self._apply_bonus_impact(ac.bonus_count, movement.type, -movement.amount)
        recalculated_bonus = self._apply_bonus_impact(base_bonus, updated["type"], updated["amount"])
        if recalculated_bonus < 0:
            messagebox.showwarning(
                "Aviso",
                f"Saldo insuficiente para esta alteração. {ac.name} ficaria com bônus negativo.",
            )
            return

        movement.type = updated["type"]
        movement.amount = updated["amount"]
        movement.description = updated["description"]
        movement.date = updated["date"]
        ac.bonus_count = recalculated_bonus

        self._show_acolyte_detail()
        self.app.save()

    def _delete_bonus_movement(self):
        """Delete the selected bonus movement."""
        if not self._current_acolyte:
            return
        sel = self._tree_bonus.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma movimentação de bônus para excluir.")
            return

        idx = self._tree_bonus.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.bonus_movements):
            return

        movement = ac.bonus_movements[idx]
        type_label = "Ganho" if movement.type == "earn" else "Uso"
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir movimentação de bônus ({type_label} {movement.amount})?",
        ):
            return

        new_bonus = self._apply_bonus_impact(ac.bonus_count, movement.type, -movement.amount)
        if new_bonus < 0:
            messagebox.showwarning(
                "Aviso",
                "Não é possível excluir esta movimentação, pois o saldo ficaria negativo.",
            )
            return

        ac.bonus_movements.pop(idx)
        ac.bonus_count = new_bonus
        self._show_acolyte_detail()
        self.app.save()

    # --------------------------------------------------------------------- #
    #  Schedule / Event History Entries
    # --------------------------------------------------------------------- #

    def _add_schedule_entry(self):
        """Add a new schedule history entry."""
        if not self._current_acolyte:
            return
        dlg = AddScheduleEntryDialog(self.app.root)
        if dlg.result:
            date, day, time, desc = dlg.result
            entry = ScheduleHistoryEntry(
                schedule_id=str(uuid.uuid4()),
                date=date,
                day=day,
                time=time,
                description=desc,
            )
            ac = self._current_acolyte
            ac.schedule_history.append(entry)
            ac.times_scheduled += 1
            self._show_acolyte_detail()
            self.refresh_list()
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
        self._sync_linked_absence(ac, "schedule", entry, False)
        ac.schedule_history.pop(idx)
        if ac.times_scheduled > 0:
            ac.times_scheduled -= 1
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _toggle_schedule_missed(self):
        if not self._current_acolyte:
            return
        sel = self._tree_schedule.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma entrada de escala para marcar/desmarcar falta.")
            return
        idx = self._tree_schedule.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.schedule_history):
            return
        entry = ac.schedule_history[idx]
        self._toggle_linked_missed_state(ac, "schedule", entry)
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _add_event_entry(self):
        """Add a new event history entry."""
        if not self._current_acolyte:
            return
        dlg = AddEventEntryDialog(self.app.root)
        if dlg.result:
            name, date, time = dlg.result
            entry = ActivityHistoryEntry(
                event_id=str(uuid.uuid4()),
                name=name,
                date=date,
                time=time,
            )
            ac = self._current_acolyte
            ac.event_history.append(entry)
            self._show_acolyte_detail()
            self.refresh_list()
            self.app.save()

    def _delete_event_entry(self):
        """Delete the selected event history entry."""
        if not self._current_acolyte:
            return
        sel = self._tree_events.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma entrada de atividade para excluir.")
            return
        idx = self._tree_events.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.event_history):
            return
        entry = ac.event_history[idx]
        if not messagebox.askyesno("Confirmar", f"Excluir entrada de atividade '{entry.name}'?"):
            return
        self._sync_linked_absence(ac, "event", entry, False)
        ac.event_history.pop(idx)
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _toggle_event_missed(self):
        if not self._current_acolyte:
            return
        sel = self._tree_events.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma entrada de atividade para marcar/desmarcar falta.")
            return
        idx = self._tree_events.index(sel[0])
        ac = self._current_acolyte
        if idx >= len(ac.event_history):
            return
        entry = ac.event_history[idx]
        self._toggle_linked_missed_state(ac, "event", entry)
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _toggle_linked_missed_state(self, ac: Acolyte, entry_type: str, entry):
        entry_id = entry.event_id if entry_type == "event" else entry.schedule_id
        linked_absence = self._find_linked_absence(ac, entry_type, entry_id)

        # If the entry is symbolic missed, toggling normal missed should convert it
        # to regular missed instead of clearing the missed state.
        if entry.missed and linked_absence and linked_absence.is_symbolic:
            linked_absence.is_symbolic = False
            return

        entry.missed = not entry.missed
        self._sync_linked_absence(ac, entry_type, entry, entry.missed)

    def _toggle_symbolic_linked_absence(self, entry_type: str):
        if not self._current_acolyte:
            return

        ac = self._current_acolyte
        if entry_type == "schedule":
            sel = self._tree_schedule.selection()
            if not sel:
                messagebox.showinfo("Aviso", "Selecione uma entrada de escala.")
                return
            idx = self._tree_schedule.index(sel[0])
            if idx >= len(ac.schedule_history):
                return
            entry = ac.schedule_history[idx]
            entry_id = entry.schedule_id
        else:
            sel = self._tree_events.selection()
            if not sel:
                messagebox.showinfo("Aviso", "Selecione uma entrada de atividade.")
                return
            idx = self._tree_events.index(sel[0])
            if idx >= len(ac.event_history):
                return
            entry = ac.event_history[idx]
            entry_id = entry.event_id

        linked_absence = self._find_linked_absence(ac, entry_type, entry_id)

        # If already symbolic, toggling symbolic should fully unmark the missed state.
        if entry.missed and linked_absence and linked_absence.is_symbolic:
            entry.missed = False
            self._sync_linked_absence(ac, entry_type, entry, False)
            self._show_acolyte_detail()
            self.app.save()
            self._refresh_calendar_views()
            return

        # If there is no linked absence yet, mark as missed first and create one.
        if not linked_absence:
            entry.missed = True
            self._sync_linked_absence(ac, entry_type, entry, True)
            linked_absence = self._find_linked_absence(ac, entry_type, entry_id)

        if not linked_absence:
            messagebox.showwarning("Aviso", "Não foi possível vincular a falta para esta entrada.")
            return

        linked_absence.is_symbolic = True
        self._show_acolyte_detail()
        self.app.save()
        self._refresh_calendar_views()

    def _toggle_schedule_symbolic_missed(self):
        self._toggle_symbolic_linked_absence("schedule")

    def _toggle_event_symbolic_missed(self):
        self._toggle_symbolic_linked_absence("event")

    # --------------------------------------------------------------------- #
    #  Unavailabilities
    # --------------------------------------------------------------------- #

    def _add_unavailability(self):
        if not self._current_acolyte:
            return
        dlg = AddUnavailabilityDialog(self.app.root)
        if dlg.result:
            day, start_time, end_time = dlg.result
            unav = Unavailability(
                id=str(uuid.uuid4()),
                day=day,
                start_time=start_time,
                end_time=end_time,
            )
            ac = self._current_acolyte
            if not hasattr(ac, 'unavailabilities') or ac.unavailabilities is None:
                ac.unavailabilities = []
            ac.unavailabilities.append(unav)
            self._show_acolyte_detail()
            self.app.save()

    def _add_temp_unavailability(self):
        if not self._current_acolyte:
            return
        dlg = AddTemporaryUnavailabilityDialog(self.app.root)
        if dlg.result:
            start_date, end_date, start_time, end_time = dlg.result
            temp = TemporaryUnavailability(
                id=str(uuid.uuid4()),
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
            )
            ac = self._current_acolyte
            if not hasattr(ac, 'temporary_unavailabilities') or ac.temporary_unavailabilities is None:
                ac.temporary_unavailabilities = []
            ac.temporary_unavailabilities.append(temp)
            self._show_acolyte_detail()
            self.app.save()

    def _edit_unavailability(self):
        if not self._current_acolyte:
            return
        sel = self._tree_unavailabilities.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma indisponibilidade para editar.")
            return
        idx = self._tree_unavailabilities.index(sel[0])
        if idx >= len(self._unav_items):
            return
        kind, item = self._unav_items[idx]
        dlg = EditUnavailabilityDialog(self.app.root, item)
        if not dlg.result:
            return
        ac = self._current_acolyte
        if kind == "regular" and dlg.result[0] == "regular":
            _, day, start_time, end_time = dlg.result
            item.day = day
            item.start_time = start_time
            item.end_time = end_time
        elif kind == "temporary" and dlg.result[0] == "temporary":
            _, start_date, end_date, start_time, end_time = dlg.result
            item.start_date = start_date
            item.end_date = end_date
            item.start_time = start_time
            item.end_time = end_time
        self._show_acolyte_detail()
        self.app.save()

    def _delete_unavailability(self):
        if not self._current_acolyte:
            return
        sel = self._tree_unavailabilities.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma indisponibilidade para excluir.")
            return
        idx = self._tree_unavailabilities.index(sel[0])
        if idx >= len(self._unav_items):
            return
        kind, item = self._unav_items[idx]
        ac = self._current_acolyte
        if kind == "regular":
            desc = f"{item.day} ({item.start_time}–{item.end_time})"
            target_list = ac.unavailabilities
        else:
            sd = self._to_short_date(item.start_date)
            ed = self._to_short_date(item.end_date)
            time_part = f" – {item.start_time}–{item.end_time}" if item.start_time else ""
            desc = f"{sd} – {ed}{time_part}"
            target_list = ac.temporary_unavailabilities
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir indisponibilidade: {desc}?"
        ):
            return
        target_list.remove(item)
        self._show_acolyte_detail()
        self.app.save()

    def _show_overview_table(self):
        """Show an overview table of all acolytes in the main panel."""
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        self._current_acolyte = None
        self.acolyte_listbox.selection_clear(0, tk.END)
        self.no_selection_label.pack_forget()
        self.detail_frame.pack_forget()

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

        columns = ("Nome", "Escalas", "Atividades", "Faltas", "Suspensões", "Bônus", "Status")
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
        overview_tree.tag_configure("future_suspension", background="#FFD699")

        sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
        for ac in sorted_acs:
            status = "Ativo"
            tag = ""
            if ac.is_suspended:
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
            else:
                has_future_suspension = False
                for s in ac.suspensions:
                    if s.is_active and s.start_date:
                        try:
                            start_dt = datetime.strptime(s.start_date, "%d/%m/%Y")
                            if start_dt.date() > datetime.now().date():
                                has_future_suspension = True
                                break
                        except ValueError:
                            pass
                if has_future_suspension:
                    status = "Será Suspendido"
                    tag = "future_suspension"

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

        def _on_row_double_click(event):
            sel = overview_tree.selection()
            if not sel:
                return
            values = overview_tree.item(sel[0], "values")
            if not values:
                return
            name = values[0]
            target = next((a for a in self.app.acolytes if a.name == name), None)
            if target is None:
                return
            # Select in listbox and open detail
            sorted_acs = sorted(self.app.acolytes, key=lambda a: a.name.lower())
            for i, ac in enumerate(sorted_acs):
                if ac.id == target.id:
                    self.acolyte_listbox.selection_clear(0, tk.END)
                    self.acolyte_listbox.selection_set(i)
                    self.acolyte_listbox.see(i)
                    break
            self._current_acolyte = target
            if hasattr(self, '_overview_frame') and self._overview_frame:
                self._overview_frame.destroy()
                self._overview_frame = None
            self._show_acolyte_detail()

        overview_tree.bind("<Double-1>", _on_row_double_click)

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

    # --------------------------------------------------------------------- #
    #  Ciclo / Report
    # --------------------------------------------------------------------- #

    def _close_cycle(self):
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        self._save_current_cycle_name()
        dlg = CloseCicloDialog(self.app.root, initial_label=self.app.current_cycle_name)
        if not dlg.result:
            return
        result = dlg.result

        if result["save_history"]:
            self.app.ciclo_history.append(
                self.app.build_current_cycle_history_entry(result["label"])
            )

        for ac in self.app.acolytes:
            if not result["keep_absences"]:
                ac.absences.clear()
            if not result["keep_schedule_data"]:
                ac.times_scheduled = 0
                ac.schedule_history.clear()
            if not result["keep_event_history"]:
                ac.event_history.clear()
            if not result["keep_bonus"]:
                ac.bonus_count = 0
                ac.bonus_movements.clear()

        if not result["keep_finalized_history"]:
            self.app.generated_schedules.clear()
            self.app.finalized_event_batches.clear()
        if not result["keep_draft_cards"]:
            self.app.schedule_slots.clear()
            self.app.general_events.clear()

        self.app.current_cycle_name = ""
        self.sync_current_cycle_name()

        if self._current_acolyte:
            self._show_acolyte_detail()
        self.refresh_list()
        self.app.save()
        self.app.schedule_tab.load_slots_from_data()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.events_tab.refresh_list()
        self.app.history_tab.refresh()
        self.app.calendar_tab.refresh()

        if result["save_history"]:
            messagebox.showinfo(
                "Concluído",
                f"Ciclo '{result['label']}' fechado e salvo no histórico!",
            )
        else:
            messagebox.showinfo(
                "Concluído",
                "Ciclo atual fechado sem salvar no histórico.",
            )

    def _generate_report(self):
        if not self.app.acolytes:
            messagebox.showinfo("Aviso", "Nenhum acólito cadastrado.")
            return
        self._save_current_cycle_name()
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
            finalized_entries = [
                entry
                for batch in self.app.finalized_event_batches
                for entry in batch.entries
            ]
            generate_report(
                sorted_acs,
                path,
                finalized_entries,
                self.app.generated_schedules,
                self.app.include_activity_table_per_acolyte,
                self.app.current_cycle_name,
            )
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
