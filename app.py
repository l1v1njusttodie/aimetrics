from flask import Flask, request, jsonify
import pandas as pd
import os
import polars as pl
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

    dl = pl.read_excel(f'./files/{filename}', read_options= {'header_row': skip_rows, 'use_columns': [year_column, country]})

    start = int(start)
    end = int(end)
    dl = dl.filter((pl.col(year_column) >= start) & (pl.col(year_column) <= end))
    dl = dl.drop_nans()
    dl = dl.rename({country: 'value', year_column: 'year'})

    y_values = dl['value'].to_list()
    x_values = dl['year'].to_list()

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