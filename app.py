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
		'sma_10': [],
		'sma_20': [],
		'sma_50': [],
		'cdl': [],
		'vol': [],
		'vol_color': []
	}
	max_vol = 0
	
	for i in data:
		if i['Volume'] > max_vol:
			max_vol = i['Volume']

		out['cdl'].append({
			'x': datetime.timestamp(i['Date']) * 1000,
			'o': i['Open'],
			'h': i['High'],
			'l': i['Low'],
			'c': i['Close']
		})
		out['sma_10'].append({
			'x': datetime.timestamp(i['Date']) * 1000,
			'y': i['SMA10']
		})
		out['sma_20'].append({
			'x': datetime.timestamp(i['Date']) * 1000,
			'y': i['SMA20']
		})
		out['sma_50'].append({
			'x': datetime.timestamp(i['Date']) * 1000,
			'y': i['SMA50']
		})
		out['vol'].append({
			'x': datetime.timestamp(i['Date']) * 1000,
			'y': i['Volume']
		})

		if i['Open'] > i['Close']:
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
  return render_template("stock-info.html")

if __name__ == "__main__":
	app.run(port="5000", debug=True)