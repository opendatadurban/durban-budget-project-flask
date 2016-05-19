import os
import sys
from flask import render_template, Flask, jsonify
import requests
if sys.version_info >= (3, 0):
    from functools import reduce

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index_mod.html')


@app.route('/api/budget/bubbletree')
def bubbletree():
    params = {
        'cut': 'demarcation.label:eThekwini|'
               + 'financial_year_end.year:2015|'
               + 'period_length.length:year|'
               + 'amount_type.label:Audited Actual|'
    }
    resp = requests.get(
        'https://data.municipalmoney.org.za/api/cubes/bsheet/facts', params)
    resp_body = resp.json()
    data = resp_body['data']
    subtotals = [{
        'amount': x['amount'],
        'label': x['item.label'],
        'order': x['item.position_in_return_form'],
        'color': '#f03e45',
        'composition': [c.replace(',', '') for c in
                        x['item.composition'].replace('sum(', '').replace(')', '').split(' ')]
    } for x in data if x['item.return_form_structure'] == 'subtotal']
    line_items = [{
        x['item.code']: {
            'amount': x['amount'],
            'label': x['item.label'],
            'color': '#f03e45',
            'order': x['item.position_in_return_form']
        }
    } for x in data if x['item.return_form_structure'] == 'line_item' or
                  x['item.return_form_structure'] == 'subtotal']
    line_items_dict = {k: v for d in line_items for k, v in d.items()}

    for subtotal in subtotals:
        if 'children' not in subtotal:
            subtotal['children'] = []
        for composition in subtotal['composition']:
            if composition in line_items_dict:
                subtotal['children'].append(line_items_dict[composition])

    amount = reduce(lambda acc, val: acc + val['amount'], subtotals, 0)
    return jsonify({
        'label': 'Total',
        'amount': amount,
        'color': '#282828',
        'children': subtotals
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
