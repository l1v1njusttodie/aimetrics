from flask import Flask, request, render_template
import pandas as pd


app = Flask(__name__)

# Глобальные переменные
uploaded_df = None
uploaded_filename = None
data = {}
countries = []
years = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global uploaded_df, uploaded_filename, data, countries, years

    selected_country = None

    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            try:
                df = pd.read_excel(file, sheet_name=None, engine='openpyxl')
            except Exception as e:
                return f"Ошибка при чтении файла: {e}"

            sheet_name = list(df.keys())[0]
            sheet = df[sheet_name]

            years = sheet.iloc[2:67, 0].astype(str).tolist()
            country_names = [str(c).strip() for c in sheet.iloc[0, 1:].tolist() if pd.notna(c)]
            gdp_values = sheet.iloc[2:67, 1:]

            data = {}
            for col_idx, country in enumerate(country_names):
                for row_idx, year in enumerate(years):
                    gdp = gdp_values.iloc[row_idx, col_idx]
                    if pd.notna(gdp):
                        gdp = float(gdp) / 1_000_000_000  # Делим на миллиарды
                    else:
                        gdp = None
                    data[(year, country)] = gdp

            countries = country_names
            uploaded_df = df
            uploaded_filename = file.filename
            selected_country = None

        else:
            selected_country = request.form.get('selected_country')
    else:
        selected_country = None

    return render_template('index.html',
                           data=data,
                           countries=countries,
                           years=years,
                           selected_country=selected_country,
                           uploaded_filename=uploaded_filename)


@app.route('/plot', methods=['GET', 'POST'])
def plot():
    global data, years, countries

    selected_country = None
    plot_data = None

    if request.method == 'POST':
        selected_country = request.form.get('selected_country')

        if selected_country in countries:
            y_values = [data.get((year, selected_country)) for year in years]
            x_values = [int(year) for year in years]

            # Сглаженные значения для разных окон
            smoothed_series = {}
            for window in range(3, 18, 2):
                smoothed = pd.Series(y_values).rolling(window=window, center=True).mean().tolist()
                smoothed_series[window] = smoothed

            plot_data = {
                'years': x_values,
                'series': smoothed_series
            }

    return render_template('plot.html',
                           countries=countries,
                           selected_country=selected_country,
                           plot_data=plot_data)
