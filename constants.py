# constants.py
# File di configurazione per l'applicazione Gestore Scout

# --- DEFINIZIONE COLONNE DATABASE ---
# Costruzione dinamica delle colonne delle specialità per 15 slot
_specialty_db_cols_list = []
for i in range(1, 16):  # Da 1 a 15
    _specialty_db_cols_list.append(f"{i} Specialità")
    _specialty_db_cols_list.append(f"Descrizione Sp {i}")
    _specialty_db_cols_list.append(f"Tipo Sp {i}")

# Lista completa delle colonne come dovrebbero apparire nel Google Sheet
DB_COLUMNS = [
    "Nome", "Cognome", "Codice Censimento", "Anno di Nascita", "Branca",
    "1 Tappa LC", "2 Tappa LC", "3 Tappa LC",
    "1 Scoperta", "2 Competenza", "3 Responsabilità",
    "1 Tappa RS", "2 Tappa RS", "3 Tappa RS",
] + _specialty_db_cols_list

# Colonne da mostrare nella Treeview principale dell'applicazione
DISPLAY_COLUMNS = [
    "Nome", "Cognome", "Codice Censimento", "Anno di Nascita", "Branca",
    "Specialità", "Ultimo Riconoscimento"
]

# Colonne per i campi di input rapido nella finestra principale
INPUT_FIELD_COLUMNS = DB_COLUMNS[:5]  # Nome, Cognome, Codice Censimento, Anno Nascita, Branca

# Colonne che devono essere visualizzate come campi di testo multiriga nel dialogo dei dettagli
MULTILINE_DETAIL_COLUMNS = [
    "1 Tappa LC", "2 Tappa LC", "3 Tappa LC",
    "1 Scoperta", "2 Competenza", "3 Responsabilità",
    "1 Tappa RS", "2 Tappa RS", "3 Tappa RS"
]

# Pattern Regex per identificare e raggruppare i campi relativi alle specialità
GENERAL_SPECIALTY_FIELDS_PATTERNS = [
    r"\d+ Specialità",
    r"Descrizione Sp \d+",
    r"Tipo Sp \d+"
]

# --- VALORI PREDEFINITI E LISTE PER LA UI ---

# Tipi di specialità per i Combobox
SPECIALITY_TYPES = ["L/C", "E/G"]

# Unità/Branche per i Combobox
UNIT_TYPES = ["Coccinelle", "Lupetti", "Quercia Rossa", "Eridano", "Clan", "Co.Ca."]

# Anni di nascita per i Combobox
BIRTH_YEARS = [str(anno) for anno in range(1980, 2031)]

# Soglia di progressione per determinare quali specialità mostrare
LC_RECOGNITION_THRESHOLD = "3 Tappa LC"

# Ordine gerarchico dei riconoscimenti/tappe per calcolare la progressione
ORDERED_RECOGNITIONS = [
    "Nessuno",  # Base
    "1 Tappa LC", "2 Tappa LC", "3 Tappa LC",
    "1 Scoperta", "2 Competenza", "3 Responsabilità",
    "1 Tappa RS", "2 Tappa RS", "3 Tappa RS"
]

# --- NOMI SPECIALITÀ (Ordinati alfabeticamente) ---
LC_SPECIALITY_NAMES = sorted([
    "Amico degli Animali", "Amico del Mare", "Amico della Natura",
    "Amico di Aronne", "Amico di Samuele", "Amico di San Francesco",
    "Artigiano", "Astronomo", "Atleta", "Attore", "Botanico",
    "Canterino", "Cercatore di Tracce", "Cittadino del Mondo",
    "Collezionista", "Cuoco", "Disegnatore", "Folclorista",
    "Fotografo", "Giardiniere", "Giocatore di Squadra",
    "Giocattolaio", "Giornalista", "Guida", "Infermiere", "Kim",
    "Maestro dei Giochi", "Maestro del Bosco", "Maestro della Salute",
    "Maestro di Danze", "Mani Abili", "Massaio", "Meteorologo",
    "Montanaro", "Musicista", "Ripara-Ricicla", "Sarto",
    "Scaccia Pericoli", "Scrittore"
])

EG_SPECIALITY_NAMES = sorted([
    "Allevatore", "Alpinista", "Amico degli animali", "Amico del quartiere",
    "Archeologo", "Artigiano", "Artista di strada", "Astronomo", "Atleta",
    "Attore", "Battelliere", "Boscaiolo", "Botanico", "Campeggiatore",
    "Canoista", "Cantante", "Carpentiere navale", "Ciclista", "Collezionista",
    "Coltivatore", "Corrispondente", "Corrispondente radio", "Cuoco",
    "Danzatore", "Disegnatore", "Elettricista", "Elettronico",
    "Esperto del computer", "Europeista", "Falegname", "Fa tutto",
    "Folclorista", "Fotografo", "Geologo", "Giardiniere", "Giocattolaio",
    "Grafico", "Guida", "Guida marina", "Hebertista", "Idraulico",
    "Infermiere", "Interprete", "Lavoratore in cuoio", "Maestro dei giochi",
    "Maestro dei nodi", "Meccanico", "Modellista", "Muratore", "Musicista",
    "Nuotatore", "Osservatore", "Osservatore meteo", "Pescatore", "Pompiere",
    "Redattore", "Regista", "Sarto", "Scenografo", "Segnalatore",
    "Servizio della Parola", "Servizio liturgico", "Servizio missionario",
    "Topografo", "Velista"
])


# --- IMPOSTAZIONI UI ---
DEFAULT_TREEVIEW_COLUMN_WIDTH = 120