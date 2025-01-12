from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import json

app = Flask(__name__)

# Membaca dataset
data = pd.read_csv('2021-2022.csv')

# Memilih kolom yang relevan
selected_columns = ['HomeTeam', 'AwayTeam', 'HTOa', 'ATOa', 'HTAt', 'ATAt',
                    'HTMid', 'ATMid', 'HTDef', 'ATDef', 'HomeAvgAge', 'AwayAvgAge',
                    'HomeMV', 'AwayMV', 'HxG', 'AxG', 'HxPTS', 'AxPTS', 'HPPDA',
                    'APPDA', 'FTR']
data = data[selected_columns]

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction = None
    selected_team1 = None
    selected_team2 = None

    if request.method == 'POST':
        # Mendapatkan tim dari form
        selected_team1 = request.form.get('team1')
        selected_team2 = request.form.get('team2')

        # Mengambil data untuk tim kandang dan tim tandang
        team1_data = data[data['HomeTeam'] == selected_team1].mean(numeric_only=True)
        team2_data = data[data['AwayTeam'] == selected_team2].mean(numeric_only=True)

        # Memperbaiki perhitungan dengan memperhitungkan hasil pertandingan sebelumnya
        # Gunakan xG rata-rata untuk tim kandang dan tandang
        team1_score = round(team1_data['HxG'])  # Menggunakan HxG untuk Home Team
        team2_score = round(team2_data['AxG'])  # Menggunakan AxG untuk Away Team

        # Memperbaiki hasil prediksi berdasarkan rata-rata xG
        if team1_score > team2_score:
            outcome = 'Home Win'
        elif team1_score < team2_score:
            outcome = 'Away Win'
        else:
            outcome = 'Draw'

        # Menyimpan hasil prediksi
        prediction = {
            'team1': selected_team1,
            'score1': team1_score,
            'team2': selected_team2,
            'score2': team2_score,
            'outcome': outcome
        }

    # Membuat grafik dengan menggunakan xG
    fig = px.scatter(
        data,
        x="HxG",
        y="AxG",
        color="FTR",
        hover_data=["HomeTeam", "AwayTeam"]
    )
    
    # Tambahkan hovertext khusus untuk digunakan dalam JavaScript
    fig.update_traces(
        hovertext=data["HomeTeam"] + " vs " + data["AwayTeam"]
    )
    graph_html = fig.to_html(full_html=False)

    # Mengambil daftar tim unik
    teams = sorted(data['HomeTeam'].unique())

    return render_template('home.html', graph_html=graph_html, teams=teams, prediction=prediction)

@app.route('/page/<int:page>', methods=['GET'])
def index(page=1):
    rows_per_page = 20
    start = (page - 1) * rows_per_page
    end = start + rows_per_page
    
    search_query = request.args.get('search', '')
    filtered_data = data  # Data yang akan difilter berdasarkan pencarian

    if search_query:
        # Filter data berdasarkan query pencarian
        filtered_data = data[data.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    table_data = filtered_data.iloc[start:end].to_dict(orient='records')
    total_pages = (len(filtered_data) + rows_per_page - 1) // rows_per_page

    # Kirim data ke template, pastikan untuk mengkonversi data ke string JSON terlebih dahulu
    table_data_json = json.dumps(filtered_data.to_dict(orient='records'))  # Semua data dalam JSON

    return render_template('index.html', table_data=table_data, table_data_json=table_data_json, page=page, total_pages=total_pages, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)
