import gspread
import webview
import json
import os

from flask import Flask, render_template, request, redirect, url_for

CREDENTIALS_FILE = 'credentials.json'
GOOGLE_SHEET_NAME = 'BACKUP Database Censiti 082025'
WORKSHEET_NAME = 'Censiti'

app = Flask(__name__)
app.debug = True
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

LOCAL = int(os.getenv('LOCAL', 0))
spreadsheet = gspread.service_account(filename=CREDENTIALS_FILE).open(GOOGLE_SHEET_NAME)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)


def get_sheet_data():
    print(type(LOCAL))
    if LOCAL == 0:
        data = worksheet.get_all_records()
        print("loaded data from drive")
        with open("tempdata.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open("tempdata.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data


@app.route("/")
def index():
    sheet_data = get_sheet_data()
    # we have to convert dictionary to list, or we get an error
    # the first 5 values are Nome, Cognome, Codice Censimento, Anno di Nascita and Branca
    basic_scout_info = [list(row_data.values())[:5] for row_data in sheet_data]
    headers = list(sheet_data[0].keys())[:5] 
    return render_template("index.html", basic_scout_info=basic_scout_info, headers=headers)


TAPPA_DISPLAY_NAMES = {
    "tappa_LC_1": "L/C 1",
    "tappa_LC_2": "L/C 2",
    "tappa_LC_3": "L/C 3",
    "tappa_scoperta": "Scoperta",
    "tappa_competenza": "Competenza",
    "tappa_responsabilita": "Responsabilità",
    "tappa_RS_1": "",
    "tappa_RS_2": "",
    "tappa_RS_3": ""
}

@app.route("/scout/<scout_id>")
def scout_detail(scout_id):
    sheet_data = get_sheet_data()
    
    # check that the scout exists and retrieve its data
    for scout in sheet_data:
        if scout['codice_censimento'] == int(scout_id): break
    
    basic_info = {
        "nome": scout.get("nome"),
        "cognome": scout.get("cognome"),
        "codice_censimento": scout.get("codice_censimento"),
        "anno_nascita": scout.get("anno_nascita"),
        "branca": scout.get("branca")
    }

    tappe = []
    for db_key, display_name in TAPPA_DISPLAY_NAMES.items():
        value = scout.get(db_key)
        if value:
            tappe.append({
                'name': display_name,
                'date': value
            })
    
    specialita = []

    for i in range(1, 10): 
        name_key = f'special_{i}'
        if not scout.get(name_key): continue

        specialita_item = {
            'name': scout.get(name_key),
            'type': scout.get(f'special_{i}_tipo'),
            'description': scout.get(f'special_{i}_desc')
        }
        specialita.append(specialita_item)

    context = {
        'scout': basic_info,
        'tappe': tappe,
        'specialita': specialita
    }

    print("--"*20)
    print(context)
    print("--"*20)
    
    return render_template("details.html", **context)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        anno_nascita = request.form.get('anno_nascita')
        codice_censimento = request.form.get('codice_censimento')
        branca = request.form.get('branca')

        # --- YOUR VALIDATION LOGIC GOES HERE ---
        
        print("--- NUOVO UTENTE RICEVUTO ---")
        print(f"Nome: {nome}")
        print(f"Cognome: {cognome}")
        print(f"Codice Censimento: {codice_censimento}")
        print(f"Anno di Nascita: {anno_nascita}")
        print(f"Branca: {branca}")
        print("----------------------------")
    
        worksheet.append_row([nome, cognome, codice_censimento, anno_nascita, branca])

        return f"""
            <h1>Utente Aggiunto con Successo!</h1>
            <p>Dati ricevuti:</p>
            <ul>
                <li>Nome: {nome}</li>
                <li>Cognome: {cognome}</li>
                <li>Anno di Nascita: {anno_nascita}</li>
                <li>Codice Censimento: {codice_censimento}</li>
                <li>Branca: {branca}</li>
            </ul>
            <a href="/add">Aggiungi un altro utente</a>
        """
    
    return render_template('add.html', years=range(2040, 1980, -1))


@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        scout_to_delete_id = request.form.get("codice_censimento")
        codici_censimento = worksheet.col_values(3)
        index_to_delete = -1
        if scout_to_delete_id in codici_censimento: index_to_delete = codici_censimento.index(scout_to_delete_id)
        if index_to_delete != -1: worksheet.delete_rows(index_to_delete + 1)

    return redirect(url_for("index"))

if __name__ == "__main__":
    # webview.create_window(f"ScoutApp", app, width=1024, height=768)
    # webview.start(debug=True)
    app.run()



# TODO: MODIFICARE SU PAGINA DETAILS.HTML MODIFICA DETTAGLI