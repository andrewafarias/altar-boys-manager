"""Classe principal da aplicação."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional

from ..data_manager import save_data, load_data, export_to_file, import_from_file
from ..models import (
    Acolyte,
    ScheduleSlot,
    GeneralEvent,
    GeneratedSchedule,
    FinalizedEventBatch,
    StandardSlot,
    CicloHistoryEntry,
)
from ..undo_manager import UndoManager
from .schedule_tab import ScheduleTab
from .events_tab import EventsTab
from .acolytes_tab import AcolytesTab
from .history_tab import HistoryTab


class App:
    """Aplicação principal de gerenciamento de escala de acólitos."""

    def __init__(self):
        self.acolytes: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []
        self.generated_schedules: List[GeneratedSchedule] = []
        self.finalized_event_batches: List[FinalizedEventBatch] = []
        self.standard_slots: List[StandardSlot] = []
        self.ciclo_history: List[CicloHistoryEntry] = []
        self.custom_common_times: List[str] = []

        self.undo_manager = UndoManager()
        self._is_restoring = False

        self.root = tk.Tk()
        self.root.title("Gerenciador de Acólitos")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        self._apply_theme()
        self._build_menu()
        self._build_notebook()
        self._load_data()

        # Push the initial state so that the very first mutation can be undone.
        self.undo_manager.push(self._capture_state())

        # Make custom_common_times accessible to time picker
        from .widgets import TimePickerDialog
        TimePickerDialog._app = self

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

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(
            label="Desfazer", command=self.undo, accelerator="Ctrl+Z"
        )
        edit_menu.add_command(
            label="Refazer", command=self.redo, accelerator="Ctrl+Y"
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)

        self.root.bind("<Control-s>", lambda e: self.save())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-Z>", lambda e: self.redo())

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.schedule_tab = ScheduleTab(self.notebook, self)
        self.events_tab = EventsTab(self.notebook, self)
        self.acolytes_tab = AcolytesTab(self.notebook, self)
        self.history_tab = HistoryTab(self.notebook, self)

        self.notebook.add(self.schedule_tab, text="📅 Criar Escala")
        self.notebook.add(self.events_tab, text="⛪ Atividades")
        self.notebook.add(self.acolytes_tab, text="👥 Acólitos")
        self.notebook.add(self.history_tab, text="📜 Histórico")

    def _load_data(self):
        result = load_data()
        (
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
            self.ciclo_history,
            self.custom_common_times,
        ) = result
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data(adapt_dates=True)
        self.events_tab.refresh_list()
        self.acolytes_tab.refresh_list()
        self.history_tab.refresh()

    def save(self):
        save_data(
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
            self.ciclo_history,
            self.custom_common_times,
        )
        if not self._is_restoring:
            self.undo_manager.push(self._capture_state())

    # -- undo / redo -------------------------------------------------------

    def _capture_state(self) -> dict:
        """Snapshot the entire application state as a plain dict."""
        return {
            "acolytes": [a.to_dict() for a in self.acolytes],
            "schedule_slots": [s.to_dict() for s in self.schedule_slots],
            "general_events": [e.to_dict() for e in self.general_events],
            "generated_schedules": [g.to_dict() for g in self.generated_schedules],
            "finalized_event_batches": [
                f.to_dict() for f in self.finalized_event_batches
            ],
            "standard_slots": [s.to_dict() for s in self.standard_slots],
            "ciclo_history": [c.to_dict() for c in self.ciclo_history],
            "custom_common_times": list(self.custom_common_times),
        }

    def _restore_state(self, state: dict) -> None:
        """Replace in-memory data with a previously captured snapshot."""
        self.acolytes = [Acolyte.from_dict(a) for a in state["acolytes"]]
        self.schedule_slots = [
            ScheduleSlot.from_dict(s) for s in state["schedule_slots"]
        ]
        self.general_events = [
            GeneralEvent.from_dict(e) for e in state["general_events"]
        ]
        self.generated_schedules = [
            GeneratedSchedule.from_dict(g) for g in state["generated_schedules"]
        ]
        self.finalized_event_batches = [
            FinalizedEventBatch.from_dict(f)
            for f in state["finalized_event_batches"]
        ]
        self.standard_slots = [
            StandardSlot.from_dict(s) for s in state["standard_slots"]
        ]
        self.ciclo_history = [
            CicloHistoryEntry.from_dict(c) for c in state["ciclo_history"]
        ]
        self.custom_common_times = list(state["custom_common_times"])

    def _refresh_all(self) -> None:
        """Refresh every tab so the UI reflects the current in-memory data."""
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data()
        self.events_tab.refresh_list()
        self.acolytes_tab.refresh_list()
        self.history_tab.refresh()

    def undo(self) -> None:
        state = self.undo_manager.undo()
        if state is None:
            return
        self._restore_state(state)
        self._is_restoring = True
        try:
            self.save()
        finally:
            self._is_restoring = False
        self._refresh_all()

    def redo(self) -> None:
        state = self.undo_manager.redo()
        if state is None:
            return
        self._restore_state(state)
        self._is_restoring = True
        try:
            self.save()
        finally:
            self._is_restoring = False
        self._refresh_all()

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
            export_to_file(
                self.acolytes,
                self.schedule_slots,
                self.general_events,
                path,
                self.generated_schedules,
                self.finalized_event_batches,
                self.standard_slots,
                self.ciclo_history,
                self.custom_common_times,
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
                ciclo_history,
                custom_common_times,
            ) = import_from_file(path)
            self.acolytes = acolytes
            self.schedule_slots = schedule_slots
            self.general_events = general_events
            self.generated_schedules = generated_schedules
            self.finalized_event_batches = finalized_event_batches
            self.standard_slots = standard_slots
            self.ciclo_history = ciclo_history
            self.custom_common_times = custom_common_times
            self.save()
            self._load_data()
            messagebox.showinfo(
                "Sucesso",
                f"Dados importados com sucesso!\n\n"
                f"{len(acolytes)} acólitos, {len(schedule_slots)} escalas, "
                f"{len(general_events)} atividades.",
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
            "- Registrar atividades\n"
            "- Gerenciar acólitos (faltas, bônus, suspensões)\n"
            "- Gerar relatórios em PDF",
        )

    def run(self):
        self.root.mainloop()
