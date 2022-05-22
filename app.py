from flask import Flask, render_template
import datetime
from db import *

app = Flask(__name__)


@app.route("/")
def home():
	data = process_cdl(get_stock_data('0005-HK', 60))
	return render_template("home.html", data=data)

@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")

def process_cdl(data):
	out = {
		'sma10': [],
		'sma20': [],
		'sma50': [],
		'cdl': [],
		'vol': [],
		'vol_color': []
	}
	max_vol = 0
	
	for i in data:
		if i['volume'] > max_vol:
			max_vol = i['volume']

		out['cdl'].append({
			'x': datetime.timestamp(i['date']) * 1000,
			'o': i['open'],
			'h': i['high'],
			'l': i['low'],
			'c': i['close']
		})

		for sma in ['sma10', 'sma20', 'sma50']:
			out[sma].append({
				'x': datetime.timestamp(i['date']) * 1000,
				'y': i[sma]
			})

		if i['open'] > i['close']:
			out['vol_color'].append('rgba(215,85,65,0.4)')
		else:
			out['vol_color'].append('rgba(80,160,115,0.4)')

	out['max_vol'] = max_vol
	return out

@app.route("/rules")
def rules():
	return render_template("rules.html")

@app.route("/stock-info")
def stock_info():
	data = process_cdl(get_stock_data('0005-HK', 60))
	return render_template("stock-info.html", data=data)

if __name__ == "__main__":
	app.run(port="5000", debug=True)