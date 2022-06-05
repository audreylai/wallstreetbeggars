from flask import Flask, render_template, request
import datetime

from matplotlib import ticker
from db import *

app = Flask(__name__)

@app.route("/")
def home():
	data = process_stock_data(get_stock_data('0005-HK', 60))
	return render_template("home.html", data=data)

@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")

@app.route("/rules")
def rules():
	return render_template("rules.html")

@app.route("/stock-list")
def stock_list():
	# GIVE ME DATA
	stock_table = get_stock_info("all")
	last_update = stock_table[0]['last_update']
	return render_template("stock-list.html", stock_table=stock_table[0]['table'], last_update=last_update, industries=stock_table[0]['industries'])

@app.route("/stock-info", methods=["GET", "POST"])
def stock_info():
	ticker = request.args.get("ticker")
	if ticker is None:
		ticker = '0005-HK'

	stock_data = process_stock_data(get_stock_data(ticker, 180))
	stock_data['ticker'] = ticker
	stock_info = get_stock_info(ticker)
		
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info)

@app.route("/stock-analytics")
def stock_analytics():
	ticker = request.args.get('ticker')
	if ticker is None:
		ticker = '0005-HK'
	
	stock_data = process_stock_data(get_stock_data(ticker, 180))
	stock_data['ticker'] = ticker
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info)

@app.route("/api/get_stock_close_pct", methods=['GET'])
def api_get_stock_close_pct():
	ticker_name = request.args.get('ticker').replace(".", "-")
	data = process_close(get_stock_data(ticker_name, 180))
	data['ticker'] = ticker_name
	return data

@app.route("/api/get_industry_close_pct", methods=['GET'])
def api_get_industry_close_pct():
	industry_name = request.args.get('industry')
	data = process_industry_avg(get_industry_close_pct(industry_name, 180))
	data['industry'] = industry_name

	return data

if __name__ == "__main__":
	app.run(port="5000", debug=True)