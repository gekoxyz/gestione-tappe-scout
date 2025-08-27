import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from queue import Queue
from typing import List, Dict, Any, Optional
import pandas as pd

import constants

from data_handler import DataHandler
import logic

class ScoutManagerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gestore Progressione Scout")
        
        self.main_content_frame = ttk.Frame(self.root, padding=10)
        self.main_content_frame.pack(fill="both", expand=True)

        self.data_handler = DataHandler()
        self.active_filters: Dict[str, str] = {}
        self.entries: Dict[str, ttk.Entry] = {}

        # Crea i widget ma lasciali disabilitati
        self.create_widgets()
        self.set_widget_state(self.widget_container, "disabled")
        
        # Mostra il messaggio di caricamento
        self.loading_label = ttk.Label(self.main_content_frame, text="Connessione a Google Sheets in corso...", font=("Arial", 16, "italic"))
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

        # Avvia la connessione in background
        self.connection_queue = Queue()
        threading.Thread(target=self.threaded_connect, daemon=True).start()
        self.root.after(100, self.check_connection_status)

    def threaded_connect(self):
        try:
            self.data_handler.connect()
            self.connection_queue.put("SUCCESS")
        except Exception as e:
            self.connection_queue.put(f"ERROR: {e}")

    def check_connection_status(self):
        try:
            message = self.connection_queue.get_nowait()
            self.loading_label.destroy() # Rimuovi il messaggio di caricamento
            
            if message == "SUCCESS":
                self.set_widget_state(self.widget_container, "normal") # Abilita tutti i widget
                self.refresh_treeview_data() # Esegui il primo caricamento dati
            else:
                detailed_message = message.replace("ERROR: ", "")
                messagebox.showerror("Errore di Connessione", f"Impossibile connettersi.\n\n{detailed_message}", parent=self.root)
                self.root.destroy()
        except Exception: # Coda ancora vuota
            self.root.after(100, self.check_connection_status)

    def set_widget_state(self, parent, state):
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            
            if widget_class in ('TButton', 'TEntry', 'TCombobox', 'Treeview'):
                try:
                    if state == 'normal':
                        if isinstance(child, ttk.Combobox):
                            child.config(state='readonly')
                        else:
                            child.config(state='normal')
                    else:
                        child.config(state=state)
                except tk.TclError:
                    pass
            
            if hasattr(child, 'winfo_children') and callable(child.winfo_children):
                if child.winfo_children():
                    self.set_widget_state(child, state)

    def create_widgets(self):
        self.widget_container = ttk.Frame(self.main_content_frame)
        self.widget_container.pack(fill="both", expand=True)

        input_frame = ttk.LabelFrame(self.widget_container, text="Dettagli Scout (Input Rapido)")
        input_frame.grid(row=0, column=0, padx=10, pady=(0,5), sticky="ew")
        
        button_frame = ttk.Frame(self.widget_container)
        button_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        list_frame = ttk.LabelFrame(self.widget_container, text="Elenco Scout")
        list_frame.grid(row=2, column=0, padx=10, pady=(5,10), sticky="nsew")

        self.widget_container.grid_rowconfigure(2, weight=1)
        self.widget_container.grid_columnconfigure(0, weight=1)

        # --- Input Frame ---
        for i, label_text in enumerate(constants.INPUT_FIELD_COLUMNS):
            ttk.Label(input_frame, text=f"{label_text}:").grid(row=0, column=i, padx=5, pady=2, sticky="w")
            
            widget = None
            default_value = '' 

            if label_text == "Anno di Nascita":
                # CHANGE HERE: Set initial state to "readonly"
                widget = ttk.Combobox(input_frame, values=constants.BIRTH_YEARS, state="readonly", width=12)
                if constants.BIRTH_YEARS:
                    default_value = constants.BIRTH_YEARS[0] 
            elif label_text == "Branca":
                # This was already "readonly"
                widget = ttk.Combobox(input_frame, values=constants.UNIT_TYPES, state="readonly", width=12)
                if "L/C" in constants.UNIT_TYPES:
                    default_value = "L/C"
                elif constants.UNIT_TYPES:
                    default_value = constants.UNIT_TYPES[0]
            else:
                widget = ttk.Entry(input_frame, width=15)
            
            if widget:
                widget.grid(row=1, column=i, padx=5, pady=(2,5), sticky="ew")
                self.entries[label_text] = widget
                
                if isinstance(widget, ttk.Combobox) and default_value:
                    widget.set(default_value)

            input_frame.grid_columnconfigure(i, weight=1)

        # --- Button Frame ---
        actions = [
            ("Aggiungi", self.add_scout), ("Aggiorna", self.update_scout_from_quick_input),
            ("Elimina", self.delete_selected_scout), ("Pulisci", self.clear_entries),
            ("Tappe/Specialità", self.open_scout_details_dialog), ("Cerca", self.open_search_scout_dialog),
            ("Mostra Tutti", self.reset_filters_and_load_all)
        ]
        for i, (text, command) in enumerate(actions):
            ttk.Button(button_frame, text=text, command=command).grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            button_frame.grid_columnconfigure(i, weight=1)
        
        # --- List Frame (Treeview) ---
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal")
        self.tree = ttk.Treeview(list_frame, columns=constants.DISPLAY_COLUMNS, show="headings",
                                 yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        for col_name in constants.DISPLAY_COLUMNS:
            self.tree.heading(col_name, text=col_name, command=lambda c=col_name: self.filter_column_dialog(c))
            width = 120
            if col_name in ["Nome", "Cognome"]: width = 150
            if col_name == "Codice Censimento": width = 100
            if col_name in ["Specialità", "Ultimo Riconoscimento"]: width = 220
            self.tree.column(col_name, width=width, minwidth=80, stretch=tk.YES)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.open_scout_details_dialog)

    def refresh_treeview_data(self, source_df_override: Optional[pd.DataFrame] = None):
        if not self.data_handler.is_connected: return
        
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        if source_df_override is not None:
            df_to_process = source_df_override
        else:
            if not self.data_handler.load_data_from_sheets():
                messagebox.showwarning("Dati Non Aggiornati", "Impossibile aggiornare i dati da Google Sheets. Potresti visualizzare dati non recenti.", parent=self.root)
            df_to_process = self.data_handler.get_all_scouts_df()

        prepared_data = logic.prepare_scout_data_for_treeview(df_to_process)
        filtered_data = self._apply_active_filters_to_display_data(prepared_data)
        self._populate_treeview(filtered_data)
        
        self.root.config(cursor="")

    def _apply_active_filters_to_display_data(self, display_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.active_filters: return display_data
        filtered_display_data = []
        for row_dict in display_data:
            match = all(str(filter_val).lower() in str(row_dict.get(col, "")).lower() for col, filter_val in self.active_filters.items())
            if match:
                filtered_display_data.append(row_dict)
        return filtered_display_data

    def _populate_treeview(self, data_to_display: List[Dict[str, Any]]):
        self.tree.delete(*self.tree.get_children())
        for row_dict in data_to_display:
            values_for_row = [row_dict.get(col, "") for col in constants.DISPLAY_COLUMNS]
            self.tree.insert("", "end", values=values_for_row)
        self.update_column_headers_with_filter_indicators()

    def update_column_headers_with_filter_indicators(self):
        for col_name in constants.DISPLAY_COLUMNS:
            header_text = col_name
            if col_name in self.active_filters:
                header_text += " 🔍"
            self.tree.heading(col_name, text=header_text, command=lambda c=col_name: self.filter_column_dialog(c))

    def add_scout(self):
        data = {col: widget.get().strip() for col, widget in self.entries.items()}
        for field in constants.INPUT_FIELD_COLUMNS:
            if not data.get(field):
                messagebox.showwarning("Campi Obbligatori", f"'{field}' non può essere vuoto.", parent=self.root)
                return
        success, msg = self.data_handler.add_scout(data)
        if success:
            self.refresh_treeview_data()
            self.clear_entries()
            messagebox.showinfo("Successo", "Nuovo scout aggiunto.", parent=self.root)
        else:
            messagebox.showerror("Errore Aggiunta", msg or "Errore sconosciuto.", parent=self.root)

    def update_scout_from_quick_input(self):
        census_code = self._get_selected_census_code_from_treeview()
        if not census_code: return
        data = {col: widget.get().strip() for col, widget in self.entries.items()}
        success, msg = self.data_handler.update_scout_general_details(census_code, data)
        if success:
            self.refresh_treeview_data()
            self.clear_entries()
            messagebox.showinfo("Successo", "Dati scout aggiornati.", parent=self.root)
        else:
            messagebox.showwarning("Errore Aggiornamento", msg or "Nessuna modifica o errore sconosciuto.", parent=self.root)

    def delete_selected_scout(self):
        census_code = self._get_selected_census_code_from_treeview()
        if not census_code: return
        scout = self.data_handler.get_scout_by_census_code(census_code)
        if scout is None: messagebox.showerror("Errore", "Scout non trovato nella cache."); return
        nome_cognome = f"{scout.get('Nome','')} {scout.get('Cognome','')}".strip()
        if messagebox.askyesno("Conferma Eliminazione", f"Eliminare lo scout '{nome_cognome}'?", parent=self.root):
            success, msg = self.data_handler.delete_scout(census_code)
            if success:
                self.refresh_treeview_data()
                self.clear_entries()
                messagebox.showinfo("Successo", "Scout eliminato.", parent=self.root)
            else:
                messagebox.showerror("Errore Eliminazione", msg or "Errore sconosciuto.", parent=self.root)

    def _get_selected_census_code_from_treeview(self) -> Optional[str]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Nessuna Selezione", "Seleziona uno scout dalla lista.", parent=self.root)
            return None
        values = self.tree.item(selected[0], "values")
        try:
            return str(values[constants.DISPLAY_COLUMNS.index("Codice Censimento")]).strip()
        except (ValueError, IndexError):
            return None

    def on_tree_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.clear_entries()
            return
        values = self.tree.item(selected[0], "values")
        self.clear_entries()
        for col_name in constants.INPUT_FIELD_COLUMNS:
            try:
                display_idx = constants.DISPLAY_COLUMNS.index(col_name)
                value = str(values[display_idx])
                if isinstance(self.entries[col_name], ttk.Combobox):
                    self.entries[col_name].set(value)
                else:
                    self.entries[col_name].insert(0, value)
            except (ValueError, IndexError): pass

    def clear_entries(self):
        for widget in self.entries.values():
            if isinstance(widget, ttk.Combobox):
                widget.set('')
            else:
                widget.delete(0, tk.END)
        if constants.INPUT_FIELD_COLUMNS:
            self.entries[constants.INPUT_FIELD_COLUMNS[0]].focus()

    def filter_column_dialog(self, column_name: str):
        val = simpledialog.askstring(f"Filtro: {column_name}", "Inserisci valore (vuoto per rimuovere):", parent=self.root, initialvalue=self.active_filters.get(column_name, ""))
        if val is not None:
            if val.strip(): self.active_filters[column_name] = val.strip()
            elif column_name in self.active_filters: del self.active_filters[column_name]
            self.refresh_treeview_data()
    
    def reset_filters_and_load_all(self):
        self.active_filters.clear()
        self.refresh_treeview_data()
        messagebox.showinfo("Filtri Rimossi", "Elenco completo ricaricato.", parent=self.root)

    def display_search_results(self, results_df: pd.DataFrame):
        self.active_filters.clear()
        self.refresh_treeview_data(source_df_override=results_df)
        if results_df.empty:
            messagebox.showinfo("Ricerca", "Nessuno scout trovato.", parent=self.root)

    def open_scout_details_dialog(self, event=None):
        from .scout_detail_dialog import ScoutDetailDialog
        census_code = self._get_selected_census_code_from_treeview()
        if census_code:
            dialog = ScoutDetailDialog(self.root, self.data_handler, census_code, self.refresh_treeview_data)
            self.root.wait_window(dialog)

    def manage_selected_scout_specialties(self):
        from .specialty_dialog import SpecialtyManagementDialog
        census_code = self._get_selected_census_code_from_treeview()
        if census_code:
            dialog = SpecialtyManagementDialog(self.root, self.data_handler, census_code, self.refresh_treeview_data)
            self.root.wait_window(dialog)

    def open_search_scout_dialog(self):
        from .search_dialog import SearchDialog
        dialog = SearchDialog(self.root, self.data_handler, self.display_search_results)
        self.root.wait_window(dialog)