# ui/search_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING: # Per evitare import circolari e per type hinting
    from data_handler import DataHandler
    import pandas as pd

class SearchDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, data_handler: 'DataHandler', 
                 display_results_callback: Callable[['pd.DataFrame'], None]):
        super().__init__(parent)
        self.title("Cerca Scout")
        self.grab_set() # Rende la finestra modale rispetto al parent
        self.resizable(False, False)

        self.data_handler = data_handler
        self.display_results_callback = display_results_callback

        self.name_entry: ttk.Entry
        self.surname_entry: ttk.Entry
        
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Gestisce la chiusura con la 'X'

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(main_frame, text="Cognome:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.surname_entry = ttk.Entry(main_frame, width=30)
        self.surname_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        main_frame.grid_columnconfigure(1, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Cerca", command=self._execute_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Annulla", command=self._on_close).pack(side="left", padx=5)

        self.name_entry.focus()

    def _execute_search(self):
        nome_query = self.name_entry.get().strip()
        cognome_query = self.surname_entry.get().strip()

        if not nome_query and not cognome_query:
            messagebox.showwarning("Input Mancante", "Inserisci Nome o Cognome per la ricerca.", parent=self)
            return

        search_results_df = self.data_handler.search_scouts(nome_query, cognome_query)

        # Il callback viene chiamato in ogni caso, sarà la finestra principale a decidere
        # cosa fare con un DataFrame vuoto (es. mostrare un messaggio).
        self.display_results_callback(search_results_df)
        
        self._on_close() # Chiude la finestra dopo la ricerca

    def _on_close(self):
        self.grab_release()
        self.destroy()