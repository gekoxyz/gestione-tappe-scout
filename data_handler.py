# data_handler.py
import gspread
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import time
import os

import constants

# file credenziali e database
CREDENTIALS_FILE_NAME = 'credentials.json'
# SPREADSHEET_NAME = 'Database Censiti'
SPREADSHEET_NAME = 'BACKUP Database Censiti 082025'
WORKSHEET_NAME = 'Censiti'

class DataHandler:
    def __init__(self):
        self.db_columns = constants.DB_COLUMNS
        self.gc: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.worksheet: Optional[gspread.Worksheet] = None
        self.df_cache = pd.DataFrame(columns=self.db_columns)
        self.is_connected = False

    def connect(self):
        """Tenta la connessione e il caricamento iniziale. Solleva ConnectionError in caso di fallimento finale."""
        if self.is_connected:
            print("INFO: Già connesso.")
            return

        self._connect_and_load_with_retry()
        self.is_connected = True

    def _connect_and_load_with_retry(self, retries=3, delay=5):
        last_exception = None
        for attempt in range(retries):
            try:
                print(f"Tentativo di connessione a Google Sheets (tentativo {attempt + 1}/{retries})...")

                CREDENTIALS_FULL_PATH = "credentials.json"

                print(f"[DEBUG] Percorso calcolato per le credenziali: '{CREDENTIALS_FULL_PATH}'")
                if not os.path.exists(CREDENTIALS_FULL_PATH):
                    print(f"[ERROR] Il file di credenziali '{CREDENTIALS_FILE_NAME}' NON è stato trovato al percorso calcolato.")
                    raise FileNotFoundError(f"Credenziali NON trovate in: {CREDENTIALS_FULL_PATH}")
                else:
                    print("[DEBUG] Credenziali trovate")

                self.gc = gspread.service_account(filename=CREDENTIALS_FULL_PATH)

                self.spreadsheet = self.gc.open(SPREADSHEET_NAME)
                self.worksheet = self.spreadsheet.worksheet(WORKSHEET_NAME)
                
                self.load_data_from_sheets()
                print(f"[INFO] Connesso a Google Sheets ('{SPREADSHEET_NAME}' -> '{WORKSHEET_NAME}') e dati caricati localmente.")
                return
            except Exception as e:
                last_exception = e
                print(f"[ERROR] Connessione non riuscita (tentativo {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    print(f"[INFO] Nuovo tentativo tra {delay} secondi...")
                    time.sleep(delay)
        raise ConnectionError(f"[ERROR] Impossibile connettersi a Google Sheets dopo {retries} tentativi.") from last_exception

    def load_data_from_sheets(self) -> bool:
        if not self.worksheet: return False
        try:
            print("[INFO] Scaricamento dati da Google Sheets...")
            all_sheet_data = self.worksheet.get_all_records(expected_headers=self.db_columns, default_blank="", numericise_ignore=['all'])
            processed_data = [{str(col): str(record.get(col, "")) for col in self.db_columns} for record in all_sheet_data]
            self.df_cache = pd.DataFrame(processed_data, columns=self.db_columns).fillna("")
            print(f"[INFO] Scaricate {len(self.df_cache)} righe.")
            return True
        except Exception as e:
            print(f"[ERRORE] Scaricamento dati fallito {e}")
            return False

    def _find_row_idx_in_sheet_by_census_code(self, census_code: str) -> Optional[int]:
        if self.df_cache.empty: return None
        matches = self.df_cache[self.df_cache["Codice Censimento"].astype(str).str.strip() == str(census_code).strip()]
        if not matches.empty:
            df_index = matches.index[0]
            print("FOND ROW IDX IN SHEET CENSUS CODE")
            print(df_index)
            return df_index + 2 
        return None

    def get_all_scouts_df(self) -> pd.DataFrame:
        return self.df_cache.copy()

    def get_scout_by_census_code(self, census_code: str) -> Optional[pd.Series]:
        matches = self.df_cache[self.df_cache["Codice Censimento"].astype(str).str.strip() == str(census_code).strip()]
        return matches.iloc[0].copy() if not matches.empty else None

    def add_scout(self, scout_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not self.worksheet: return False, "[ERROR] No connessione internet al foglio di lavoro"
        cod_census = str(scout_data.get("Codice Censimento", "")).strip()
        if not cod_census: return False, "'Codice Censimento' è obbligatorio."
        if cod_census in self.df_cache["Codice Censimento"].astype(str).str.strip().values:
            return False, f"[ERROR] Codice Censimento '{cod_census}' già esistente."
        row_values = [str(scout_data.get(col, "")).strip() for col in self.db_columns]
        try:
            self.worksheet.append_row(row_values, value_input_option='USER_ENTERED')
            self.load_data_from_sheets()
            return True, None
        except Exception as e:
            return False, f"Errore API Google: {str(e)}"

    def delete_scout(self, census_code: str) -> Tuple[bool, Optional[str]]:
        if not self.worksheet: return False, "[ERROR] No connessione internet al foglio di lavoro"
        row_idx_sheet = self._find_row_idx_in_sheet_by_census_code(census_code)
        if row_idx_sheet is None:
            return False, "[ERROR] Scout non trovato per l'eliminazione."
        try:
            self.worksheet.delete_rows(int(row_idx_sheet)) # cast to int because int64 of numpy makes gspread crash
            self.load_data_from_sheets()
            return True, None
        except Exception as e:
            return False, f"Errore API Google: {str(e)}"

    def update_scout_general_details(self, original_census_code: str, updated_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        row_idx_sheet = self._find_row_idx_in_sheet_by_census_code(original_census_code)
        if row_idx_sheet is None:
            return False, f"Scout con codice '{original_census_code}' non trovato."
            
        nuovo_cod_census = str(updated_data.get("Codice Censimento", original_census_code)).strip()
        if nuovo_cod_census != original_census_code:
            other_scouts_df = self.df_cache[self.df_cache["Codice Censimento"] != original_census_code]
            if nuovo_cod_census in other_scouts_df["Codice Censimento"].astype(str).str.strip().values:
                return False, f"Il Codice Censimento '{nuovo_cod_census}' esiste già."
        
        cells_to_update = []
        try:
            df_index = row_idx_sheet - 2
            if df_index < 0 or df_index >= len(self.df_cache):
                return False, f"Errore di coerenza: indice {df_index} fuori dai limiti della cache."

            scout_series_from_cache = self.df_cache.iloc[df_index]

            for i, col_name in enumerate(self.db_columns):
                if col_name in updated_data:
                    new_value = str(updated_data[col_name]).strip()
                    old_value = str(scout_series_from_cache.get(col_name, "")).strip()
                    if old_value != new_value:
                        cells_to_update.append(gspread.Cell(row_idx_sheet, i + 1, new_value))

            if not cells_to_update:
                return False, "Nessuna modifica rilevata."
                
            self.worksheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
            self.load_data_from_sheets()
            return True, None
        except Exception as e:
            return False, f"Errore API Google: {str(e)}"

    def update_scout_specialty(self, census_code: str, slot_number: int, name: str, description: str, specialty_type: str) -> bool:
        return self._update_specialty_cells(census_code, slot_number, name, description, specialty_type)

    def remove_scout_specialty(self, census_code: str, slot_number: int) -> bool:
        return self._update_specialty_cells(census_code, slot_number, "", "", "")

    def _update_specialty_cells(self, census_code, slot_number, name, description, specialty_type):
        row_idx_sheet = self._find_row_idx_in_sheet_by_census_code(census_code)
        if row_idx_sheet is None: return False
        try:
            header = self.db_columns
            cols_to_update = {
                f"{slot_number} Specialità": name,
                f"Descrizione Sp {slot_number}": description,
                f"Tipo Sp {slot_number}": specialty_type
            }
            cells = []
            for col_name, value in cols_to_update.items():
                if col_name in header:
                    col_idx = header.index(col_name) + 1
                    cells.append(gspread.Cell(row_idx_sheet, col_idx, str(value).strip()))
            
            if not cells: 
                print(f"ATTENZIONE: Nessuna colonna di specialità corrispondente trovata per lo slot {slot_number}")
                return False
                
            self.worksheet.update_cells(cells, value_input_option='USER_ENTERED')
            self.load_data_from_sheets()
            return True
        except Exception as e:
            print(f"Errore gspread update specialty: {e}")
            return False
            
    def get_specialties_for_scout(self, census_code: str) -> List[Dict[str, Any]]:
        scout_series = self.get_scout_by_census_code(census_code)
        if scout_series is None: return []
        specialties = []
        for i in range(1, 16):
            spec_name = scout_series.get(f"{i} Specialità")
            if spec_name:
                specialties.append({
                    "slot": i, 
                    "name": spec_name, 
                    "description": scout_series.get(f"Descrizione Sp {i}", ""), 
                    "type": scout_series.get(f"Tipo Sp {i}", "")
                })
        return specialties
    
    def search_scouts(self, name_query: str = "", surname_query: str = "") -> pd.DataFrame:
        df = self.df_cache.copy()
        conds = pd.Series([True] * len(df))
        if name_query: conds &= df["Nome"].str.lower().str.contains(name_query.lower(), na=False)
        if surname_query: conds &= df["Cognome"].str.lower().str.contains(surname_query.lower(), na=False)
        return df[conds]