# logic.py
import pandas as pd
from typing import List, Dict, Any
import constants # Importa le configurazioni

def calculate_last_recognition(scout_series: pd.Series) -> str:
    """
    Calcola l'ultimo riconoscimento per uno scout.
    scout_series: una riga (pd.Series) dal DataFrame degli scout.
    """
    last_recognition = "Nessuno"
    # Usa config.ORDERED_RECOGNITIONS
    for rec_col in reversed(constants.ORDERED_RECOGNITIONS[1:]): # Salta "Nessuno" all'inizio della lista per il check
        if str(scout_series.get(rec_col, "")).strip(): # Se il campo ha un valore
            last_recognition = rec_col
            break
    return last_recognition

def get_visible_specialties_for_display(scout_series: pd.Series, last_recognition: str) -> List[str]:
    """
    Determina quali nomi di specialità mostrare per uno scout nella colonna "Specialità" della UI.
    scout_series: una riga (pd.Series) dal DataFrame degli scout.
    last_recognition: l'ultimo riconoscimento calcolato per lo scout.
    """
    visible_specialties_names = []
    try:
        # Usa config.ORDERED_RECOGNITIONS e config.LC_RECOGNITION_THRESHOLD
        last_rec_index = constants.ORDERED_RECOGNITIONS.index(last_recognition)
        threshold_index = constants.ORDERED_RECOGNITIONS.index(constants.LC_RECOGNITION_THRESHOLD)
    except ValueError: # Se un riconoscimento non è nella lista (non dovrebbe accadere)
        # Fallback sicuro, magari logga un avviso
        last_rec_index = 0 # Considera come "Nessuno"
        threshold_index = constants.ORDERED_RECOGNITIONS.index(constants.LC_RECOGNITION_THRESHOLD)

    show_lc_type = last_rec_index <= threshold_index

    for i in range(1, 16): # Da 1 a 15 (o usa una costante da config per il max numero di specialità)
        spec_name_val = str(scout_series.get(f"{i} Specialità", "")).strip()
        spec_type_val = str(scout_series.get(f"Tipo Sp {i}", "")).strip()

        if not spec_name_val: # Salta se non c'è nome
            continue

        if show_lc_type: # Se dobbiamo mostrare L/C
            # Mostra L/C o se tipo è vuoto (consideralo L/C di default per retrocompatibilità)
            if spec_type_val == "L/C" or not spec_type_val:
                visible_specialties_names.append(spec_name_val)
        else: # Dobbiamo mostrare E/G (perché last_rec_index > threshold_index)
            if spec_type_val == "E/G":
                visible_specialties_names.append(spec_name_val)
    
    return visible_specialties_names


def prepare_scout_data_for_treeview(scouts_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Prepara i dati degli scout per la visualizzazione nella Treeview principale.
    Calcola 'Ultimo Riconoscimento' e 'Specialità'.
    """
    processed_rows = []
    for _, scout_series in scouts_df.iterrows():
        display_row = {}
        # Popola con le colonne dirette
        for col_name in constants.DB_COLUMNS: # Prendi tutte le colonne base
            if col_name in constants.DISPLAY_COLUMNS: # Se è una colonna da mostrare direttamente
                 display_row[col_name] = scout_series.get(col_name, "")

        # Calcola campi derivati
        last_rec = calculate_last_recognition(scout_series)
        display_row["Ultimo Riconoscimento"] = last_rec

        visible_specs = get_visible_specialties_for_display(scout_series, last_rec)
        display_row["Specialità"] = ", ".join(visible_specs) if visible_specs else "Nessuna"
        
        # Assicurati che tutte le display_columns siano presenti nel dizionario, anche se vuote
        # Questo serve per popolare correttamente la treeview con self.tree.insert("", "end", values=...)
        final_display_row = {col: display_row.get(col, "") for col in constants.DISPLAY_COLUMNS}
        processed_rows.append(final_display_row)
        
    return processed_rows