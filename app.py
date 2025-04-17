from flask import Flask, request, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)


@app.route('/upload', methods=['POST'])
def upload():
    if not os.path.exists('./files'):
        os.makedirs('./files')

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
        smoothed = [value if not pd.isna(value) else None for value in smoothed]
        smoothed_series[window] = smoothed

    plot_data = {
        'years': x_values,
        'series': smoothed_series
    }
    app.logger.info(plot_data)

    return jsonify(plot_data), 200