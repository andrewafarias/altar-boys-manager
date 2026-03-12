"""Aba de histórico de escalas e atividades finalizadas."""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from ..models import ScheduleSlot, Acolyte, CicloHistoryEntry
from ..report_generator import generate_report
from .dialogs import CloseCicloDialog


class HistoryTab(ttk.Frame):
    """Aba de histórico de escalas geradas e atividades finalizadas."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        self._merged_frame = ttk.Frame(nb)
        self._ciclo_frame = ttk.Frame(nb)
        nb.add(self._merged_frame, text="📚 Escalas e Atividades")
        nb.add(self._ciclo_frame, text="🔄 Histórico de Ciclos")

        self._build_merged_history()
        self._build_ciclo_history()

    # --------------------------------------------------------------------- #
    #  Merged Schedule + Activity History
    # --------------------------------------------------------------------- #

    def _build_merged_history(self):
        self._merged_items = []

        paned = tk.PanedWindow(
            self._merged_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5
        )
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(left, text="Escalas e Atividades", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._merged_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._merged_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._merged_listbox.yview)
        self._merged_listbox.bind("<<ListboxSelect>>", self._on_merged_select)

        ttk.Button(left, text="✏️ Editar Escala", command=self._edit_schedule).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(left, text="🗑️ Excluir Lote", command=self._delete_merged_batch).pack(
            fill=tk.X, pady=4
        )

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._merged_detail_label = ttk.Label(
            right, text="Selecione um lote para ver os detalhes.", foreground="gray"
        )
        self._merged_detail_label.pack(pady=20)

        self._merged_detail_frame = ttk.Frame(right)

        # --- Schedule section ---
        self._merged_sched_section = ttk.Frame(self._merged_detail_frame)

        ttk.Label(
            self._merged_sched_section, text="Texto da Escala:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        txt_frame = ttk.Frame(self._merged_sched_section)
        txt_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(txt_frame)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._merged_sched_text = tk.Text(
            txt_frame, width=50, height=12, yscrollcommand=sb2.set,
            state=tk.DISABLED, font=("Courier", 9)
        )
        self._merged_sched_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.config(command=self._merged_sched_text.yview)

        # --- Unified units table ---
        self._merged_units_section = ttk.Frame(self._merged_detail_frame)

        ttk.Label(
            self._merged_units_section, text="Unidades do Lote:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(6, 2))

        units_frame = ttk.Frame(self._merged_units_section)
        units_frame.pack(fill=tk.BOTH, expand=True)
        sb_units = ttk.Scrollbar(units_frame, orient=tk.VERTICAL)
        sb_units.pack(side=tk.RIGHT, fill=tk.Y)
        self._merged_units_tree = ttk.Treeview(
            units_frame,
            columns=("Tipo", "Nome", "Data", "Hora", "Acólitos"),
            show="headings",
            height=8,
            yscrollcommand=sb_units.set,
        )
        sb_units.config(command=self._merged_units_tree.yview)
        for col, w in [("Tipo", 100), ("Nome", 140), ("Data", 70), ("Hora", 60), ("Acólitos", 200)]:
            self._merged_units_tree.heading(col, text=col)
            self._merged_units_tree.column(col, width=w, minwidth=40)
        self._merged_units_tree.pack(fill=tk.BOTH, expand=True)

        units_btn_frame = ttk.Frame(self._merged_units_section)
        units_btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(
            units_btn_frame, text="🗑️ Excluir Unidade Selecionada", command=self._delete_unit_entry
        ).pack(side=tk.LEFT, padx=2)

    # --------------------------------------------------------------------- #
    #  Refresh
    # --------------------------------------------------------------------- #

    def refresh(self):
        """Atualiza as listas."""
        self._refresh_merged_list()
        self._refresh_ciclo_list()

    def _compute_merged_items(self):
        """Build list of (schedule, batch) pairs for the unified history view."""
        items = []
        referenced_batch_ids = set()
        batch_by_id = {fb.id: fb for fb in self.app.finalized_event_batches}

        for gs in self.app.generated_schedules:
            batch = None
            if gs.batch_id and gs.batch_id in batch_by_id:
                batch = batch_by_id[gs.batch_id]
                referenced_batch_ids.add(gs.batch_id)
            items.append({"schedule": gs, "batch": batch})

        # Orphaned batches with no associated schedule
        for fb in self.app.finalized_event_batches:
            if fb.id not in referenced_batch_ids:
                items.append({"schedule": None, "batch": fb})

        return items

    def _refresh_merged_list(self):
        self._merged_items = self._compute_merged_items()
        self._merged_listbox.delete(0, tk.END)
        for item in self._merged_items:
            gs = item["schedule"]
            fb = item["batch"]
            if gs is not None and fb is not None:
                label = f"{gs.generated_at} ({len(gs.slots)} horário(s) + {len(fb.entries)} atividade(s))"
            elif gs is not None:
                label = f"{gs.generated_at} ({len(gs.slots)} horário(s))"
            else:
                label = f"⛪ {fb.finalized_at} ({len(fb.entries)} atividade(s))"
            self._merged_listbox.insert(tk.END, label)

    # --------------------------------------------------------------------- #
    #  Selection Handler
    # --------------------------------------------------------------------- #

    def _on_merged_select(self, event=None):
        sel = self._merged_listbox.curselection()
        if not sel:
            self._merged_detail_label.pack(pady=20)
            self._merged_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self._merged_items):
            return
        item = self._merged_items[idx]
        gs = item["schedule"]
        fb = item["batch"]

        self._merged_detail_label.pack_forget()
        self._merged_detail_frame.pack(fill=tk.BOTH, expand=True)

        if gs is not None:
            self._merged_sched_section.pack(fill=tk.BOTH, expand=True, before=self._merged_units_section)
            self._merged_sched_text.config(state=tk.NORMAL)
            self._merged_sched_text.delete("1.0", tk.END)
            self._merged_sched_text.insert(tk.END, gs.schedule_text)
            self._merged_sched_text.config(state=tk.DISABLED)
        else:
            self._merged_sched_section.pack_forget()

        # Populate unified units table
        self._merged_units_section.pack(fill=tk.BOTH, expand=True)
        self._merged_units_tree.delete(*self._merged_units_tree.get_children())
        self._units_data = []  # store unit references for deletion

        if gs is not None:
            for slot in gs.slots:
                if slot.is_general_event:
                    unit_type = "Escala Geral"
                else:
                    unit_type = "Escala"
                names = []
                for aid in slot.acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac:
                        names.append(ac.name)
                self._merged_units_tree.insert(
                    "", tk.END,
                    values=(unit_type, slot.description or "-", slot.date, slot.time or "-", ", ".join(names) or "-")
                )
                self._units_data.append({"kind": "schedule_slot", "slot": slot, "schedule": gs})

        if fb is not None:
            for entry in fb.entries:
                names = []
                for aid in entry.participating_acolyte_ids:
                    ac = self.app.find_acolyte(aid)
                    if ac:
                        names.append(ac.name)
                self._merged_units_tree.insert(
                    "", tk.END,
                    values=("Atividade", entry.name, entry.date, entry.time or "-", ", ".join(names) or "-")
                )
                self._units_data.append({"kind": "event_entry", "entry": entry, "batch": fb})

    # --------------------------------------------------------------------- #
    #  Edit Schedule
    # --------------------------------------------------------------------- #

    def _edit_schedule(self):
        """Load a generated schedule back into the schedule tab for editing."""
        sel = self._merged_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma escala para editar.")
            return
        idx = sel[0]
        if idx >= len(self._merged_items):
            return
        item = self._merged_items[idx]
        gs = item["schedule"]
        if gs is None:
            messagebox.showinfo("Aviso", "Este lote não possui escala para editar.")
            return
        if not messagebox.askyesno(
            "Editar Escala",
            f"Deseja carregar a escala de {gs.generated_at} para edição?\n\n"
            "As contagens dos acólitos serão revertidas e a escala será movida para a aba de criação.\n"
            "Horários existentes na aba de criação serão descartados.",
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

        # Discard currently edited schedule slots/cards before loading snapshot
        self.app.schedule_slots.clear()

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
        self.app.generated_schedules.remove(gs)
        self.app.save()

        # Refresh UI
        self._refresh_merged_list()
        self._merged_detail_label.pack(pady=20)
        self._merged_detail_frame.pack_forget()
        self.app.schedule_tab.load_slots_from_data()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()

        # Switch to schedule tab
        self.app.notebook.select(self.app.schedule_tab)
        messagebox.showinfo("Concluído", "Escala carregada para edição na aba 'Criar Escala'.")

    # --------------------------------------------------------------------- #
    #  Delete Batch (schedule + activities together)
    # --------------------------------------------------------------------- #

    def _delete_merged_batch(self):
        sel = self._merged_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um lote para excluir.")
            return
        idx = sel[0]
        if idx >= len(self._merged_items):
            return
        item = self._merged_items[idx]
        gs = item["schedule"]
        fb = item["batch"]

        label = gs.generated_at if gs else fb.finalized_at
        parts = []
        if gs:
            parts.append(f"{len(gs.slots)} horário(s)")
        if fb:
            parts.append(f"{len(fb.entries)} atividade(s)")
        desc = " e ".join(parts)

        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o lote de {label} ({desc})?\n\n"
            "Isso reverterá as contagens dos acólitos envolvidos.",
        ):
            return

        if gs:
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
            self.app.generated_schedules.remove(gs)

        if fb:
            event_ids = {e.event_id for e in fb.entries}
            for ac in self.app.acolytes:
                ac.event_history = [e for e in ac.event_history if e.event_id not in event_ids]
            self.app.finalized_event_batches.remove(fb)

        self.app.save()
        self._refresh_merged_list()
        self._merged_detail_label.pack(pady=20)
        self._merged_detail_frame.pack_forget()
        self.app.acolytes_tab.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        messagebox.showinfo("Concluído", "Lote excluído e contagens revertidas.")

    def _delete_unit_entry(self):
        """Delete a single unit (schedule slot or event entry) from the selected batch."""
        sel = self._merged_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um lote.")
            return
        idx = sel[0]
        if idx >= len(self._merged_items):
            return

        tree_sel = self._merged_units_tree.selection()
        if not tree_sel:
            messagebox.showinfo("Aviso", "Selecione uma unidade para excluir.")
            return
        unit_idx = self._merged_units_tree.index(tree_sel[0])
        if unit_idx >= len(self._units_data):
            return

        unit_data = self._units_data[unit_idx]

        if unit_data["kind"] == "schedule_slot":
            slot = unit_data["slot"]
            gs = unit_data["schedule"]
            desc = slot.description or "Escala"
            if not messagebox.askyesno(
                "Confirmar",
                f"Excluir a unidade '{desc}' de {slot.date}?\n\n"
                "Isso reverterá as contagens dos acólitos envolvidos.",
            ):
                return

            # Reverse acolyte changes for this slot
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    if ac.times_scheduled > 0:
                        ac.times_scheduled -= 1
                    ac.schedule_history = [
                        e for e in ac.schedule_history if e.schedule_id != slot.slot_id
                    ]

            gs.slots.remove(slot)

            # If no more slots and no linked batch, remove the schedule entirely
            if not gs.slots:
                item = self._merged_items[idx]
                if item["batch"] is None:
                    self.app.generated_schedules.remove(gs)

        elif unit_data["kind"] == "event_entry":
            entry = unit_data["entry"]
            fb = unit_data["batch"]
            if not messagebox.askyesno(
                "Confirmar",
                f"Excluir a atividade '{entry.name}' de {entry.date}?\n\n"
                f"Isso removerá o registro de atividade dos {len(entry.participating_acolyte_ids)} acólito(s) participantes.",
            ):
                return

            for ac in self.app.acolytes:
                ac.event_history = [e for e in ac.event_history if e.event_id != entry.event_id]

            fb.entries.remove(entry)

            # If no more entries and no linked schedule, remove the batch
            if not fb.entries:
                item = self._merged_items[idx]
                if item["schedule"] is None:
                    self.app.finalized_event_batches.remove(fb)

        self.app.save()
        self._refresh_merged_list()
        self._on_merged_select()
        self.app.acolytes_tab.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        messagebox.showinfo("Concluído", "Unidade excluída do lote.")

    # --------------------------------------------------------------------- #
    #  Ciclo History
    # --------------------------------------------------------------------- #

    def _build_ciclo_history(self):
        paned = tk.PanedWindow(
            self._ciclo_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5
        )
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(left, text="Histórico de Ciclos", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._ciclo_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._ciclo_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._ciclo_listbox.yview)
        self._ciclo_listbox.bind("<<ListboxSelect>>", self._on_ciclo_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="🔄 Restaurar Ciclo", command=self._restore_ciclo).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="📄 Gerar Relatório PDF", command=self._generate_ciclo_report).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🗑️ Excluir Ciclo", command=self._delete_ciclo).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🧹 Limpar Histórico", command=self._clear_ciclo_history).pack(fill=tk.X, pady=2)

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._ciclo_detail_label = ttk.Label(
            right, text="Selecione um ciclo para ver os detalhes.", foreground="gray"
        )
        self._ciclo_detail_label.pack(pady=20)

        self._ciclo_detail_frame = ttk.Frame(right)

        ttk.Label(
            self._ciclo_detail_frame, text="Acólitos no ciclo:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        ac_frame = ttk.Frame(self._ciclo_detail_frame)
        ac_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(ac_frame, orient=tk.VERTICAL)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._ciclo_tree = ttk.Treeview(
            ac_frame,
            columns=("Nome", "Escalas", "Atividades", "Faltas", "Bônus"),
            show="headings",
            yscrollcommand=sb2.set,
        )
        sb2.config(command=self._ciclo_tree.yview)
        for col, w in [("Nome", 180), ("Escalas", 70), ("Atividades", 80), ("Faltas", 60), ("Bônus", 60)]:
            self._ciclo_tree.heading(col, text=col)
            self._ciclo_tree.column(col, width=w, minwidth=40)
        self._ciclo_tree.pack(fill=tk.BOTH, expand=True)

    def _refresh_ciclo_list(self):
        self._ciclo_listbox.delete(0, tk.END)
        for ch in self.app.ciclo_history:
            self._ciclo_listbox.insert(tk.END, f"{ch.label} ({ch.closed_at})")

    def _on_ciclo_select(self, event=None):
        sel = self._ciclo_listbox.curselection()
        if not sel:
            self._ciclo_detail_label.pack(pady=20)
            self._ciclo_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self.app.ciclo_history):
            return
        ch = self.app.ciclo_history[idx]
        self._ciclo_detail_label.pack_forget()
        self._ciclo_detail_frame.pack(fill=tk.BOTH, expand=True)

        self._ciclo_tree.delete(*self._ciclo_tree.get_children())
        for ac_dict in ch.acolytes_snapshot:
            name = ac_dict.get("name", "?")
            escalas = ac_dict.get("times_scheduled", 0)
            atividades = len(ac_dict.get("event_history", []))
            faltas = len(ac_dict.get("absences", []))
            bonus = ac_dict.get("bonus_count", 0)
            self._ciclo_tree.insert("", tk.END, values=(name, escalas, atividades, faltas, bonus))

    def _restore_ciclo(self):
        sel = self._ciclo_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um ciclo para restaurar.")
            return
        idx = sel[0]
        if idx >= len(self.app.ciclo_history):
            return
        ch = self.app.ciclo_history[idx]
        pre_restore = CloseCicloDialog(
            self.app.root,
            initial_label=self.app.current_cycle_name,
            title_text="Restaurar Ciclo",
            action_text="Continuar",
            show_retention_options=False,
            info_title="Antes de restaurar o ciclo selecionado:",
        )
        if not pre_restore.result:
            return

        save_current = pre_restore.result["save_history"]
        if save_current:
            self.app.ciclo_history.append(
                self.app.build_current_cycle_history_entry(pre_restore.result["label"])
            )

        if not messagebox.askyesno(
            "Confirmar Restauração",
            f"Deseja restaurar o ciclo '{ch.label}' ({ch.closed_at})?\n\n"
            "O estado atual será substituído pelo ciclo selecionado.",
        ):
            if save_current:
                self.app.ciclo_history.pop()
            return

        from ..models import (
            Acolyte, ScheduleSlot, GeneralEvent,
            GeneratedSchedule, FinalizedEventBatch,
        )

        # Restore the selected cycle
        self.app.acolytes = [Acolyte.from_dict(a) for a in ch.acolytes_snapshot]
        self.app.schedule_slots = [ScheduleSlot.from_dict(s) for s in ch.schedule_slots_snapshot]
        self.app.general_events = [GeneralEvent.from_dict(e) for e in ch.general_events_snapshot]
        self.app.generated_schedules = [GeneratedSchedule.from_dict(gs) for gs in ch.generated_schedules_snapshot]
        self.app.finalized_event_batches = [FinalizedEventBatch.from_dict(fb) for fb in ch.finalized_event_batches_snapshot]

        self.app.save()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.schedule_tab.load_slots_from_data()
        self.app.events_tab.refresh_list()
        self.app.acolytes_tab.sync_current_cycle_name()
        self.app.acolytes_tab.refresh_list()
        self.refresh()
        self.app.calendar_tab.refresh()

        messagebox.showinfo(
            "Concluído",
            f"Estado restaurado para o ciclo '{ch.label}'."
            + (f"\nO ciclo anterior foi salvo." if save_current else "")
        )

    def _generate_ciclo_report(self):
        sel = self._ciclo_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um ciclo para gerar o relatório.")
            return
        idx = sel[0]
        if idx >= len(self.app.ciclo_history):
            return
        ch = self.app.ciclo_history[idx]

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Salvar relatório do ciclo como",
            initialfile=f"relatorio_{ch.label.replace(' ', '_')}.pdf",
        )
        if not path:
            return

        try:
            from ..models import Acolyte, FinalizedEventBatchEntry, FinalizedEventBatch, GeneratedSchedule
            acolytes = sorted(
                [Acolyte.from_dict(a) for a in ch.acolytes_snapshot],
                key=lambda a: a.name.lower()
            )
            generated_schedules = [GeneratedSchedule.from_dict(gs) for gs in ch.generated_schedules_snapshot]
            # Reconstruct finalized event entries from snapshot
            finalized_entries = []
            for fb_dict in ch.finalized_event_batches_snapshot:
                fb = FinalizedEventBatch.from_dict(fb_dict)
                finalized_entries.extend(fb.entries)

            generate_report(
                acolytes,
                path,
                finalized_entries,
                generated_schedules,
                self.app.include_activity_table_per_acolyte,
                ch.label,
            )
            if messagebox.askyesno(
                "Sucesso",
                f"Relatório do ciclo '{ch.label}' gerado em:\n{path}\n\nDeseja abrir?"
            ):
                self._open_file(path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{e}")

    def _delete_ciclo(self):
        sel = self._ciclo_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um ciclo para excluir.")
            return
        idx = sel[0]
        if idx >= len(self.app.ciclo_history):
            return
        ch = self.app.ciclo_history[idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o ciclo '{ch.label}' ({ch.closed_at}) do histórico?\n\n"
            "Essa ação não pode ser desfeita."
        ):
            return
        self.app.ciclo_history.pop(idx)
        self.app.save()
        self._refresh_ciclo_list()
        self._ciclo_detail_label.pack(pady=20)
        self._ciclo_detail_frame.pack_forget()
        messagebox.showinfo("Concluído", "Ciclo excluído do histórico.")

    def _clear_ciclo_history(self):
        if not self.app.ciclo_history:
            messagebox.showinfo("Aviso", "O histórico de ciclos já está vazio.")
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Limpar todo o histórico de ciclos ({len(self.app.ciclo_history)} ciclo(s))?\n\n"
            "Essa ação não pode ser desfeita."
        ):
            return
        self.app.ciclo_history.clear()
        self.app.save()
        self._refresh_ciclo_list()
        self._ciclo_detail_label.pack(pady=20)
        self._ciclo_detail_frame.pack_forget()
        messagebox.showinfo("Concluído", "Histórico de ciclos limpo.")

    def _open_file(self, path: str):
        try:
            if sys.platform.startswith("darwin"):
                subprocess.call(["open", path])
            elif sys.platform.startswith("win"):
                os.startfile(path)
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            pass
