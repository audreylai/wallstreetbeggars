from flask import Flask, render_template, request
import datetime
import re

from db import *

app = Flask(__name__)

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


@app.route("/stock-list")
def stock_list():
	stock_table = get_stock_info("all")
	last_update = stock_table['last_update']
	return render_template("stock-list.html", stock_table=stock_table['table'], last_update=last_update, industries=stock_table['industries'])


@app.route("/stock-info", methods=["GET", "POST"])
def stock_info():
	if request.method == "POST":
		ticker = request.form.get("ticker")
	else:
		ticker = request.args.get('ticker')
	if ticker is None:
		ticker = '0005-HK'

	print(ticker)
	stock_data = process_stock_data(get_stock_data(ticker, 180), 1)
	stock_data['ticker'] = ticker
	stock_info = get_stock_info(ticker)
	statistics = {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower(): stock_data[key] for key in ["close", "volume", "sma10", "sma20", "sma50", "rsi"]} | {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower() : stock_info[key] for key in ["previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"] if key in stock_info}
		
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, statistics=statistics)


@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	try:
		if request.method == "POST":
			ticker = request.form.get("ticker")
			period = request.form.get("period", type=int)
			interval = request.form.get("interval", type=int)
		else:
			ticker = request.args.get('ticker')
			period = request.args.get("period", type=int)
			interval = request.args.get("interval", type=int)

		period = 180 if period is None else period
		interval = 1 if interval is None else interval

	except:
		return '400 bad request', 400 # need a proper error page for this

	if ticker is None:
		ticker = '0005-HK' # default HSBC
	
	stock_data = process_stock_data(get_stock_data(ticker, period), interval)
	stock_data['ticker'], stock_data['period'], stock_data['interval'] = ticker, period, interval
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info, industries=get_industries())


@app.route("/api/get_stock_data", methods=['GET'])
def api_get_stock_data():
	try:
		ticker = request.args.get('ticker').replace(".", "-")
		period = request.args.get('period', type=int)
		interval = request.args.get('interval', type=int)
		if period is None or interval is None:
			raise Exception
	except:
		return {}, 400

	data = process_stock_data(get_stock_data(ticker, period), interval)
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	return data


@app.route("/api/get_stock_close_pct", methods=['GET'])
def api_get_stock_close_pct():
	try:
		ticker = request.args.get('ticker').replace(".", "-")
		period = request.args.get('period', type=int)
		interval = request.args.get('interval', type=int)
		if period is None or interval is None:
			raise Exception
	except:
		return {}, 400

	data = process_stock_data(get_stock_data(ticker, period), interval, include=['close_pct'])
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	return data


@app.route("/api/get_industry_close_pct", methods=['GET'])
def api_get_industry_close_pct():
	try:
		industry = request.args.get('industry')
		period = request.args.get('period', type=int)
		interval = request.args.get('interval', type=int)
		if period is None or interval is None:
			raise Exception
	except:
		return {}, 400
	
	data = process_industry_avg(get_industry_close_pct(industry, period), interval)
	data['industry'], data['period'], data['interval'] = industry, period, interval
	return data

if __name__ == "__main__":
	app.run(port="5000", debug=True)