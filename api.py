from flask import request
from db import *
from app import app
import json

@app.route("/api/get_stock_data", methods=['GET'])
def api_get_stock_data():
	ticker = request.args.get('ticker', type=str)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int)

	if period is None or period <= 0: return {}, 400
	if interval is None or interval <= 0: return {}, 400
	if ticker is None: 
		return {}, 400
	else:
		ticker = ticker.upper().replace(".", "-")

	data = process_stock_data(get_stock_data(ticker, period), interval)
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	return json.dumps(data)


@app.route("/api/get_stock_close_pct", methods=['GET'])
def api_get_stock_close_pct():
	ticker = request.args.get('ticker', type=str)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int)

	if period is None or period <= 0: return {}, 400
	if interval is None or interval <= 0: return {}, 400
	if ticker is None: 
		return {}, 400
	else:
		ticker = ticker.upper().replace(".", "-")

	data = process_stock_data(get_stock_data(
		ticker, period), interval, include=['close_pct'])
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	return data


@app.route("/api/get_industry_close_pct", methods=['GET'])
def api_get_industry_close_pct():
	industry = request.args.get('industry', type=str)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int)

	if period is None or period <= 0: return {}, 400
	if interval is None or interval <= 0: return {}, 400
	if industry is None: return {}, 400
	
	data = process_industry_avg(get_industry_close_pct(industry, period), interval)
	data['industry'], data['period'], data['interval'] = industry, period, interval
	return data