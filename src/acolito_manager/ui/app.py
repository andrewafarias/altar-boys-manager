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
)
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
        ) = result
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data()
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
            export_to_file(
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
            ) = import_from_file(path)
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
