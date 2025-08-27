# ui/specialty_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, List, Optional, TYPE_CHECKING

try:
    import constants
except ImportError:
    print("ERRORE CRITICO: constants.py non trovato.")
    exit()

if TYPE_CHECKING:
    from data_handler import DataHandler
    from .scout_detail_dialog import ScoutDetailDialog

class SpecialtyManagementDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, data_handler: 'DataHandler',
                 census_code: str, refresh_callback: Callable[[], None]):
        super().__init__(parent)
        self.main_app_parent = parent
        self.data_handler = data_handler
        self.census_code = census_code
        self.refresh_callback = refresh_callback

        scout_series = self.data_handler.get_scout_by_census_code(self.census_code)
        scout_name_display = ""
        if scout_series is not None and not scout_series.empty:
            scout_name_display = f" per {scout_series.get('Nome','')} {scout_series.get('Cognome','')}"

        self.title(f"Gestione Specialità Scout{scout_name_display}")
        self.geometry("850x700")
        self.grab_set()
        self.resizable(True, True)

        # Variabili Tkinter
        self.spec_type_var = tk.StringVar()
        self.spec_name_var = tk.StringVar()
        self.editing_slot_var = tk.StringVar(value="")

        # Riferimenti ai Widget
        self.specialties_tree: ttk.Treeview
        self.spec_name_combo: ttk.Combobox
        self.spec_desc_edit_text: tk.Text
        self.full_desc_text_widget: tk.Text
        self.add_update_button: ttk.Button
        
        self._create_widgets()
        self._populate_specialties_tree()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # --- Frame Superiore (con grid) ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(pady=5, fill="x", expand=False)
        top_frame.grid_columnconfigure(0, weight=3) # Treeview più larga
        top_frame.grid_columnconfigure(1, weight=2) # Frame di editing

        # Frame Treeview
        list_frame = ttk.LabelFrame(top_frame, text="Specialità Attuali")
        list_frame.grid(row=0, column=0, padx=(0, 10), sticky="nswe")
        spec_cols = ("Slot", "Tipo", "Nome Specialità", "Anteprima Descrizione")
        self.specialties_tree = ttk.Treeview(list_frame, columns=spec_cols, show="headings", height=8)
        self.specialties_tree.heading("Slot", text="Slot", anchor="center"); self.specialties_tree.column("Slot", width=40, anchor="center", stretch=tk.NO)
        self.specialties_tree.heading("Tipo", text="Tipo", anchor="w"); self.specialties_tree.column("Tipo", width=60, anchor="w", stretch=tk.NO)
        self.specialties_tree.heading("Nome Specialità", text="Nome", anchor="w"); self.specialties_tree.column("Nome Specialità", width=180)
        self.specialties_tree.heading("Anteprima Descrizione", text="Anteprima", anchor="w"); self.specialties_tree.column("Anteprima Descrizione", width=200)
        spec_scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.specialties_tree.yview)
        self.specialties_tree.configure(yscrollcommand=spec_scrollbar_y.set)
        spec_scrollbar_y.pack(side="right", fill="y")
        self.specialties_tree.pack(side="left", fill="both", expand=True)
        self.specialties_tree.bind("<<TreeviewSelect>>", self._on_specialty_select_in_tree)

        # Frame Editing
        edit_frame = ttk.LabelFrame(top_frame, text="Aggiungi/Modifica Dati")
        edit_frame.grid(row=0, column=1, sticky="nswe", padx=(5, 0))
        edit_frame.grid_columnconfigure(1, weight=1)
        
        # Widget interni a edit_frame
        ttk.Label(edit_frame, text="Tipo:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        spec_type_combo = ttk.Combobox(edit_frame, textvariable=self.spec_type_var, values=constants.SPECIALITY_TYPES, state="readonly", width=38)
        spec_type_combo.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        if constants.SPECIALITY_TYPES: self.spec_type_var.set(constants.SPECIALITY_TYPES[0])
        self.spec_type_var.trace_add("write", self._update_spec_name_options)
        
        ttk.Label(edit_frame, text="Nome:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.spec_name_combo = ttk.Combobox(edit_frame, textvariable=self.spec_name_var, values=[], width=38, state="readonly") # state="normal" per nomi custom
        self.spec_name_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        self._update_spec_name_options()

        ttk.Label(edit_frame, text="Descrizione:").grid(row=2, column=0, padx=5, pady=3, sticky="nw")
        desc_text_frame = ttk.Frame(edit_frame)
        desc_text_frame.grid(row=2, column=1, padx=5, pady=3, sticky="ewns")
        self.spec_desc_edit_text = tk.Text(desc_text_frame, width=35, height=4, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        desc_edit_scrollbar = ttk.Scrollbar(desc_text_frame, orient="vertical", command=self.spec_desc_edit_text.yview)
        self.spec_desc_edit_text.config(yscrollcommand=desc_edit_scrollbar.set)
        desc_edit_scrollbar.pack(side="right", fill="y")
        self.spec_desc_edit_text.pack(side="left", fill="both", expand=True)
        
        action_buttons_frame = ttk.Frame(edit_frame)
        action_buttons_frame.grid(row=3, column=0, columnspan=3, pady=(10, 5), sticky="ew")
        self.add_update_button = ttk.Button(action_buttons_frame, text="Aggiungi Nuova", command=self._add_or_update_specialty)
        self.add_update_button.pack(side="left", padx=5)
        ttk.Button(action_buttons_frame, text="Rimuovi Selez.", command=self._remove_selected_specialty).pack(side="left", padx=5)
        ttk.Button(action_buttons_frame, text="Pulisci", command=self._clear_input_fields).pack(side="left", padx=5)

        # --- Frame Inferiore Descrizione ---
        desc_display_frame = ttk.LabelFrame(main_frame, text="Visualizzazione Descrizione Completa")
        desc_display_frame.pack(pady=10, fill="both", expand=True)
        self.full_desc_text_widget = tk.Text(desc_display_frame, wrap=tk.WORD, state=tk.DISABLED, height=6, relief=tk.FLAT, background=self.cget('bg'))
        full_desc_scrollbar = ttk.Scrollbar(desc_display_frame, orient="vertical", command=self.full_desc_text_widget.yview)
        self.full_desc_text_widget.config(yscrollcommand=full_desc_scrollbar.set)
        full_desc_scrollbar.pack(side="right", fill="y")
        self.full_desc_text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # --- Barra Bottoni Inferiore ---
        bottom_button_bar = ttk.Frame(main_frame, borderwidth=1, relief="groove")
        bottom_button_bar.pack(fill="x", pady=(10, 5), padx=5, side="bottom")
        ttk.Button(bottom_button_bar, text="Vedi Dettagli Generali", command=self._open_detail_dialog).pack(side="left", padx=10, pady=5)
        ttk.Button(bottom_button_bar, text="Chiudi Gestione Specialità", command=self._on_close).pack(side="right", padx=10, pady=5)

    def _update_spec_name_options(self, *args):
        selected_type = self.spec_type_var.get()
        current_name = self.spec_name_var.get()
        if selected_type == "L/C":
            self.spec_name_combo['values'] = constants.LC_SPECIALITY_NAMES
        elif selected_type == "E/G":
            self.spec_name_combo['values'] = constants.EG_SPECIALITY_NAMES
        else:
            self.spec_name_combo['values'] = []
        if current_name not in self.spec_name_combo['values']:
             self.spec_name_var.set("")

    def _populate_specialties_tree(self):
        self.specialties_tree.delete(*self.specialties_tree.get_children())
        scout_specialties = self.data_handler.get_specialties_for_scout(self.census_code)
        for spec_data in scout_specialties:
            slot, name, desc_full, spec_type = spec_data.get("slot"), spec_data.get("name"), spec_data.get("description"), spec_data.get("type")
            if not spec_type and name: spec_type = constants.SPECIALITY_TYPES[0]
            desc_preview = (desc_full[:47] + "...") if len(desc_full) > 50 else desc_full
            self.specialties_tree.insert("", "end", values=(slot, spec_type, name, desc_preview), tags=(str(slot), desc_full, spec_type))
        self._clear_input_fields()

    def _clear_input_fields(self):
        if constants.SPECIALITY_TYPES: self.spec_type_var.set(constants.SPECIALITY_TYPES[0])
        else: self.spec_type_var.set("")
        self.spec_desc_edit_text.delete("1.0", tk.END)
        self.full_desc_text_widget.config(state=tk.NORMAL)
        self.full_desc_text_widget.delete("1.0", tk.END)
        self.full_desc_text_widget.config(state=tk.DISABLED)
        self.editing_slot_var.set("")
        self.add_update_button.config(text="Aggiungi Nuova")
        if self.specialties_tree.selection(): self.specialties_tree.selection_remove(self.specialties_tree.selection())

    def _on_specialty_select_in_tree(self, event=None):
        selected = self.specialties_tree.selection()
        if not selected: self._clear_input_fields(); return
        item_data = self.specialties_tree.item(selected[0])
        slot, desc_full, spec_type = item_data["tags"]
        name = item_data["values"][2]
        self.spec_type_var.set(spec_type or (constants.SPECIALITY_TYPES[0] if constants.SPECIALITY_TYPES else ""))
        self.spec_name_var.set(name)
        self.spec_desc_edit_text.delete("1.0", tk.END); self.spec_desc_edit_text.insert("1.0", desc_full)
        self.full_desc_text_widget.config(state=tk.NORMAL)
        self.full_desc_text_widget.delete("1.0", tk.END); self.full_desc_text_widget.insert("1.0", desc_full)
        self.full_desc_text_widget.config(state=tk.DISABLED)
        self.editing_slot_var.set(slot)
        self.add_update_button.config(text=f"Salva Modifiche (Slot {slot})")

    def _add_or_update_specialty(self):
        name = self.spec_name_var.get().strip()
        spec_type = self.spec_type_var.get()
        desc = self.spec_desc_edit_text.get("1.0", tk.END).strip()
        if not name or not spec_type:
            messagebox.showwarning("Input Mancante", "Nome e Tipo della Specialità sono obbligatori.", parent=self)
            return

        is_update = bool(self.editing_slot_var.get())
        if is_update:
            target_slot_idx = int(self.editing_slot_var.get())
        else:
            occupied_slots = {spec['slot'] for spec in self.data_handler.get_specialties_for_scout(self.census_code)}
            target_slot_idx = next((i for i in range(1, 16) if i not in occupied_slots), -1)
            if target_slot_idx == -1:
                messagebox.showerror("Limite Raggiunto", "Tutti i 15 slot per le specialità sono occupati.", parent=self)
                return
        
        # --- Logica Cursore di Attesa ---
        self.config(cursor="watch")
        self.update_idletasks()

        try:
            # Esegui l'operazione lunga
            success = self.data_handler.update_scout_specialty(
                self.census_code, target_slot_idx, name, desc, spec_type
            )
            
            # Gestisci il risultato
            if success:
                action_verb = "aggiornata" if is_update else "aggiunta"
                messagebox.showinfo("Successo", f"Specialità '{name}' {action_verb} con successo.", parent=self)
                self._populate_specialties_tree()
                self.refresh_callback()
            else:
                messagebox.showerror("Errore", "Impossibile salvare la specialità su Google Sheets.", parent=self)
        
        finally:
            # --- Ripristina il Cursore ---
            self.config(cursor="")

    def _remove_selected_specialty(self):
        selected = self.specialties_tree.selection()
        if not selected: messagebox.showwarning("Nessuna Selezione", "Seleziona una specialità da rimuovere.", parent=self); return
        item_data = self.specialties_tree.item(selected[0])
        slot, name = item_data["tags"][0], item_data["values"][2]
        if not messagebox.askyesno("Conferma Rimozione", f"Rimuovere la specialità '{name}' dallo slot {slot}?", parent=self): return
        
        # --- Logica Cursore di Attesa ---
        self.config(cursor="watch")
        self.update_idletasks()

        try:
            # Esegui l'operazione lunga
            success = self.data_handler.remove_scout_specialty(self.census_code, int(slot))
            
            # Gestisci il risultato
            if success:
                messagebox.showinfo("Successo", f"Specialità '{name}' rimossa.", parent=self)
                self._populate_specialties_tree()
                self.refresh_callback()
            else:
                messagebox.showerror("Errore", "Impossibile rimuovere la specialità da Google Sheets.", parent=self)

        finally:
            # --- Ripristina il Cursore ---
            self.config(cursor="")
            
    def _open_detail_dialog(self):
        # Import locale per evitare import circolare
        from .scout_detail_dialog import ScoutDetailDialog
        
        detail_dialog = ScoutDetailDialog(
            parent=self.main_app_parent,
            data_handler=self.data_handler,
            census_code=self.census_code,
            refresh_callback=self.refresh_callback
        )
        self._on_close()

    def _on_close(self):
        self.grab_release()
        self.destroy()