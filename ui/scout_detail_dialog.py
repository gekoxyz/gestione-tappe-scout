# ui/scout_detail_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, TYPE_CHECKING, Optional
import pandas as pd

import constants

if TYPE_CHECKING:
    from data_handler import DataHandler
    from .specialty_dialog import SpecialtyManagementDialog

class ScoutDetailDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, data_handler: 'DataHandler',
                 census_code: str, refresh_callback: Callable[[], None]):
        super().__init__(parent)
        self.main_app_parent = parent
        self.data_handler = data_handler
        self.original_census_code = census_code
        self.refresh_callback = refresh_callback

        self.scout_data_series = self.data_handler.get_scout_by_census_code(self.original_census_code)

        if self.scout_data_series is None or self.scout_data_series.empty:
            messagebox.showerror("Errore Dati", f"Scout con Codice Censimento '{self.original_census_code}' non trovato.", parent=self.main_app_parent)
            self.destroy()
            return

        self.title(f"Dettagli Scout: {self.scout_data_series.get('Nome','')} {self.scout_data_series.get('Cognome','')}")
        self.geometry("750x700")
        self.grab_set()
        self.resizable(True, True)

        self.detail_widgets: Dict[str, Any] = {}
        
        self._create_widgets()
        self._populate_fields()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # Frame principale che usa grid per il layout
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- Canvas e Scrollbar ---
        canvas = tk.Canvas(main_frame)
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding="5")
        
        canvas.configure(yscrollcommand=scrollbar_y.set)
        
        # Posiziona canvas e scrollbar con grid
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Binding per lo scroll (semplificato)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", _on_mousewheel)


        # --- Titolo e Campi di Input nel scrollable_frame ---
        ttk.Label(self.scrollable_frame, text=f"Dati di {self.scout_data_series.get('Nome','')} {self.scout_data_series.get('Cognome','')}", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")
        
        current_row = 1
        for col_name in constants.DB_COLUMNS:
            is_specialty_field = any(pd.Series([col_name]).str.match(pattern).any() for pattern in constants.GENERAL_SPECIALTY_FIELDS_PATTERNS)
            if is_specialty_field:
                continue

            label = ttk.Label(self.scrollable_frame, text=f"{col_name}:")
            label.grid(row=current_row, column=0, padx=5, pady=3, sticky="ne")
            label.bind("<MouseWheel>", _on_mousewheel) # Anche le label fanno scrollare
            
            widget = None
            if col_name in constants.MULTILINE_DETAIL_COLUMNS:
                # Frame per contenere Text widget e la sua scrollbar
                text_frame = ttk.Frame(self.scrollable_frame)
                text_frame.grid(row=current_row, column=1, padx=5, pady=3, sticky="ewns")
                widget = tk.Text(text_frame, width=50, height=3, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
                scrollbar_text = ttk.Scrollbar(text_frame, orient="vertical", command=widget.yview)
                widget.config(yscrollcommand=scrollbar_text.set)
                scrollbar_text.pack(side="right", fill="y")
                widget.pack(side="left", fill="both", expand=True)
                widget.bind("<MouseWheel>", lambda e: "break") # Impedisce la propagazione dello scroll
            elif col_name == "Anno di Nascita":
                widget = ttk.Combobox(self.scrollable_frame, values=constants.BIRTH_YEARS, state="readonly")
            elif col_name == "Branca":
                widget = ttk.Combobox(self.scrollable_frame, values=constants.UNIT_TYPES, state="readonly")
            else: # Per Nome, Cognome, Codice Censimento
                widget = ttk.Entry(self.scrollable_frame)

            if widget and not isinstance(widget, tk.Text): # Posiziona widget non-Text
                widget.grid(row=current_row, column=1, padx=5, pady=3, sticky="ew")
            
            if widget:
                self.detail_widgets[col_name] = widget
            
            current_row += 1
        
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # --- Barra dei Bottoni (figlia di main_frame) ---
        button_bar = ttk.Frame(main_frame)
        button_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(button_bar, text="Gestisci Specialità", command=self._open_specialty_management).pack(side="left", padx=5, pady=5)
        ttk.Button(button_bar, text="Chiudi", command=self._on_close).pack(side="right", padx=5, pady=5)
        ttk.Button(button_bar, text="Salva Modifiche", command=self._save_details).pack(side="right", padx=5, pady=5)

    def _populate_fields(self):
        """Popola i campi del form con i dati dello scout."""
        if self.scout_data_series is None: return

        for col_name, widget in self.detail_widgets.items():
            value = str(self.scout_data_series.get(col_name, ""))
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", value)
            elif isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, value)
            elif isinstance(widget, ttk.Combobox):
                widget.set(value)

    def _save_details(self):
        """Raccoglie i dati, li valida e chiama il DataHandler per salvare."""
        updated_data: Dict[str, str] = {}
        for col_name, widget in self.detail_widgets.items():
            if isinstance(widget, tk.Text):
                updated_data[col_name] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                updated_data[col_name] = widget.get().strip()

        # Validazione UI
        if not updated_data.get("Codice Censimento"):
            messagebox.showerror("Errore Validazione", "'Codice Censimento' non può essere vuoto.", parent=self)
            return
        if updated_data.get("Anno di Nascita") and not updated_data["Anno di Nascita"].isdigit():
            messagebox.showerror("Errore Validazione", "'Anno di Nascita' deve essere un numero.", parent=self)
            return

        # --- Logica Cursore di Attesa ---
        self.config(cursor="watch") # Cambia il cursore per questa finestra di dialogo
        self.update_idletasks()     # Forza l'aggiornamento della UI

        try:
            # Esegui l'operazione lunga
            success, error_message = self.data_handler.update_scout_general_details(
                self.original_census_code, 
                updated_data
            )

            # Gestisci il risultato
            if success:
                messagebox.showinfo("Successo", "Dati generali aggiornati su Google Sheets.", parent=self)
                self.refresh_callback()

                # Aggiorna i dati interni del dialogo
                new_census_code = updated_data.get("Codice Censimento")
                if new_census_code and new_census_code != self.original_census_code:
                    self.original_census_code = new_census_code
                
                self.scout_data_series = self.data_handler.get_scout_by_census_code(self.original_census_code)
                print(f"SCOUT DATA SERIES -> {self.scout_data_series}")
                self._populate_fields()
                self.title(f"Dettagli Scout: {self.scout_data_series.get('Nome','')} {self.scout_data_series.get('Cognome','')}")
            else:
                messagebox.showwarning("Errore Aggiornamento", error_message or "Nessuna modifica rilevata o errore sconosciuto.", parent=self)
        
        finally:
            # --- Ripristina il Cursore ---
            # Questo blocco viene eseguito SEMPRE, sia che il try abbia successo o fallisca.
            self.config(cursor="")

    def _open_specialty_management(self):
        # Import locale per evitare import circolare
        from .specialty_dialog import SpecialtyManagementDialog
        
        specialty_dialog = SpecialtyManagementDialog(
            parent=self.main_app_parent,
            data_handler=self.data_handler,
            census_code=self.original_census_code,
            refresh_callback=self.refresh_callback
        )
        self._on_close()

    def _on_close(self):
        self.grab_release()
        self.destroy()