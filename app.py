import datetime
import re
from math import ceil

from flask import Flask, render_template, request

app = Flask(__name__)

import api
from db import *


@app.template_filter('epoch_convert')
def timectime(s):
	return datetime.fromtimestamp(s).strftime('%d/%m/%y')


@app.route("/")
def home():
	data = process_stock_data(get_stock_data('0005-HK', 60), 1)
	return render_template("home.html", data=data)


@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")


@app.route("/rules")
def rules():
	return render_template("rules.html")


# @app.route("/stock-list")
# def stock_list():
# 	stock_table = get_stock_info("ALL")
# 	active_tickers = get_active_tickers("test")['active']
# 	last_updated = stock_table['last_updated'].strftime("%d/%m/%Y")
# 	return render_template("stock-list.html", stock_table=stock_table['table'], last_updated=last_updated, industries=stock_table['industries'], active_tickers=active_tickers)


@app.route("/stock-list", methods=["GET", "POST"])
def stock_list_page():
	if request.method == "POST":
		page = request.form.get("page", type=int)
		sort_col = request.form.get("sort_col", type=str)
		sort_dir_str = request.form.get("sort_dir", type=str)
	else:
		page = request.args.get("page", type=int)
		sort_col = request.args.get("sort_col", type=str)
		sort_dir_str = request.args.get("sort_dir", type=str)

	if page is None: page = 1
	if sort_col is None: sort_col = 'ticker'
	if sort_dir_str == 'desc':
		sort_dir = pymongo.DESCENDING
	else:
		sort_dir = pymongo.ASCENDING

	stock_table = get_stock_info("ALL", sort_col, sort_dir)

	rows_per_page = 20
	num_of_pages = ceil(len(stock_table["table"]) / rows_per_page)

	page = max(1, min(page, num_of_pages))
	stock_table["table"] = stock_table["table"][rows_per_page*(page-1):min(rows_per_page*page+1, len(stock_table["table"]))]	

	active_tickers = get_active_tickers("test")['active']
	last_updated = stock_table['last_updated'].strftime("%d/%m/%Y")
	return render_template("stock-list.html", stock_table=stock_table['table'], last_updated=last_updated, industries=stock_table['industries'], active_tickers=active_tickers, num_of_pages=num_of_pages, page=page, sort_col=sort_col, sort_dir=sort_dir)


@app.route("/update-active", methods=["POST"])
def update_active():
	# write update db logic
	print(request.form.get("check"), request.form.getlist("tickers[]"))
	if request.form.get("check") == "true":
		update_active_tickers("test", request.form.getlist("tickers[]"))
	else:
		delete_active_tickers("test", request.form.getlist("tickers[]"))
	return {"tickers": request.form.getlist("tickers[]")}


@app.route("/stock-info", methods=["POST", "GET"])
def stock_info():
	if request.method == "POST":
		ticker = request.form.get("ticker", type=str)
	else:
		ticker = request.args.get("ticker", type=str)

	if ticker is None:
		ticker = '0005-HK'
	else:
		ticker = ticker.upper().replace(".", "-")

	stock_data = process_stock_data(get_stock_data(ticker, 180), 1)
	stock_data['ticker'] = ticker
	stock_info = get_stock_info(ticker)
	statistics = {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower(): stock_data[key] for key in ["close", "volume", "sma10", "sma20", "sma50", "rsi"]} | {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower() : stock_info[key] for key in ["previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"] if key in stock_info}
		
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, statistics=statistics)


@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	if request.method == "POST":
		ticker = request.form.get("ticker", type=str)
		period = request.form.get("period", type=int)
		interval = request.form.get("interval", type=int)
	else:
		ticker = request.args.get('ticker', type=str)
		period = request.args.get("period", type=int)
		interval = request.args.get("interval", type=int)

	if ticker is None:
		ticker = '0005-HK'
	else:
		ticker = ticker.upper().replace(".", "-")

	if period is None or period <= 0: period = 180
	if interval is None or interval <= 0: interval = 1
	
	stock_data = process_stock_data(get_stock_data(ticker, period), interval)
	stock_data['ticker'], stock_data['period'], stock_data['interval'] = ticker, period, interval
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info, industries=get_all_industries(), indexes=get_all_tickers(ticker_type='index'))


if __name__ == "__main__":
	app.run(port="5000", debug=True)
