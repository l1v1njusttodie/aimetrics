from flask import Flask, request, render_template, jsonify
import pandas as pd


app = Flask(__name__)

# Глобальные переменные
# uploaded_df = None
# uploaded_filename = None
# data = {}
# countries = []
# years = []

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     global uploaded_df, uploaded_filename, data, countries, years
#
#     selected_country = None
#
#     if request.method == 'POST':
#         file = request.files.get('file')
#         if file:
#             try:
#                 df = pd.read_excel(file, sheet_name=None, engine='openpyxl')
#             except Exception as e:
#                 return f"Ошибка при чтении файла: {e}"
#
#             sheet_name = list(df.keys())[0]
#             sheet = df[sheet_name]
#
#             years = sheet.iloc[2:67, 0].astype(str).tolist()
#             country_names = [str(c).strip() for c in sheet.iloc[0, 1:].tolist() if pd.notna(c)]
#             gdp_values = sheet.iloc[2:67, 1:]
#
#             data = {}
#             for col_idx, country in enumerate(country_names):
#                 for row_idx, year in enumerate(years):
#                     gdp = gdp_values.iloc[row_idx, col_idx]
#                     if pd.notna(gdp):
#                         gdp = float(gdp) / 1_000_000_000  # Делим на миллиарды
#                     else:
#                         gdp = None
#                     data[(year, country)] = gdp
#
#             countries = country_names
#             uploaded_df = df
#             uploaded_filename = file.filename
#             selected_country = None
#
#         else:
#             selected_country = request.form.get('selected_country')
#     else:
#         selected_country = None
#
#     return render_template('index.html',
#                            data=data,
#                            countries=countries,
#                            years=years,
#                            selected_country=selected_country,
#                            uploaded_filename=uploaded_filename)


# @app.route('/plot', methods=['GET', 'POST'])
# def plot():
#     global data, years, countries
#
#     selected_country = None
#     plot_data = None
#
#     if request.method == 'POST':
#         selected_country = request.form.get('selected_country')
#
#         if selected_country in countries:
#             y_values = [data.get((year, selected_country)) for year in years]
#             x_values = [int(year) for year in years]
#
#             # Сглаженные значения для разных окон
#             smoothed_series = {}
#             for window in range(3, 18, 2):
#                 smoothed = pd.Series(y_values).rolling(window=window, center=True).mean().tolist()
#                 smoothed_series[window] = smoothed
#
#             plot_data = {
#                 'years': x_values,
#                 'series': smoothed_series
#             }
#
#     return render_template('plot.html',
#                            countries=countries,
#                            selected_country=selected_country,
#                            plot_data=plot_data)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    file.save("./files/" + file.filename)
    app.logger.info(file.filename)
    return jsonify({'filename': file.filename}), 200


@app.route('/graph-data', methods=['GET'])
def get_graph_data():
    args = request.args
    app.logger.info(args)
    start = args.get('start')
    end = args.get('end')
    country = args.get('country')
    year_column = args.get('yearColumn')
    filename = args.get('filename')
    skip_rows = int(args.get('skipRows'))

    if start is None or end is None or country is None or filename is None:
        return jsonify({'error': 'Missing required parameters'}), 400

    raw_df = pd.read_excel(f'./files/{filename}', skiprows=skip_rows)
    df = pd.DataFrame(raw_df[(raw_df.iloc[:, 0] >= int(start)) & (raw_df.iloc[:, 0] <= int(end))], columns=[year_column, country])
    df = df.dropna()
    app.logger.info(df.info)
    df = df.rename(columns={country: 'value'})
    df['year'] = df.iloc[:, 0].astype(int)
    df = df[['year', 'value']].to_dict('records')

    y_values = [entry['value'] for entry in df]
    x_values = [entry['year'] for entry in df]

    # Сглаженные значения для разных окон
    smoothed_series = {}
    for window in range(3, 18, 2):
        smoothed = pd.Series(y_values).rolling(window=window, center=True).mean().tolist()
        smoothed_series[window] = smoothed

    plot_data = {
        'years': x_values,
        'series': smoothed_series
    }

    return jsonify(plot_data), 200