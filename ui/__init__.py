import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Dict, Any, Optional # Potrebbe servire ancora per type hinting
import pandas as pd
import constants

from data_handler import DataHandler

import logic

class ScoutManagerApp: # o MainAppWindow
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gestore Progressione Scout")

        self.data_handler = DataHandler(
            data_file_path=constants.DATA_FILE_NAME,
            db_columns=constants.DB_COLUMNS
        )

        self.active_filters: Dict[str, str] = {}
        self.entries: Dict[str, ttk.Entry] = {}


        self.create_widgets()
        self.refresh_treeview_data()

    def _prepare_data_for_display(self, df_to_process: pd.DataFrame) -> List[Dict[str, Any]]:
        processed_rows = []
        for _, scout_series in df_to_process.iterrows():
            row_dict = {}
            for col_name in constants.DISPLAY_COLUMNS:
                if col_name in scout_series:
                    row_dict[col_name] = scout_series[col_name]
                else:
                    row_dict[col_name] = ""

            last_recognition = "Nessuno"
            for rec_col in reversed(constants.ORDERED_RECOGNITIONS):
                if str(scout_series.get(rec_col, "")).strip():
                    last_recognition = rec_col
                    break
            row_dict["Ultimo Riconoscimento"] = last_recognition

            visible_specialties = []
            try:
                last_rec_index = constants.ORDERED_RECOGNITIONS.index(last_recognition)
                threshold_index = constants.ORDERED_RECOGNITIONS.index(constants.LC_RECOGNITION_THRESHOLD)
            except ValueError:
                last_rec_index = 0
                threshold_index = constants.ORDERED_RECOGNITIONS.index(constants.LC_RECOGNITION_THRESHOLD)

            show_lc_type = last_rec_index <= threshold_index

            for i in range(1, 16):
                spec_name_val = str(scout_series.get(f"{i} Specialità", "")).strip()
                spec_type_val = str(scout_series.get(f"Tipo Sp {i}", "")).strip()

                if not spec_name_val: continue

                if show_lc_type:
                    if spec_type_val == "L/C" or not spec_type_val:
                        visible_specialties.append(spec_name_val)
                else:
                    if spec_type_val == "E/G":
                        visible_specialties.append(spec_name_val)

            row_dict["Specialità"] = ", ".join(visible_specialties) if visible_specialties else "Nessuna"
            processed_rows.append(row_dict)
        return processed_rows
