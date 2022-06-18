import json
from flask import request, Blueprint

from db import *
from utils import *

bp = Blueprint('app', __name__)

@bp.route('/api/get_stock_data', methods=['GET'])
def api_get_stock_data():
	ticker = request.args.get('ticker', type=str, default='0005-HK').upper().replace(".", "-")
	start_epoch = request.args.get("start_epoch", type=int)
	end_epoch = request.args.get("end_epoch", type=int)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int, default=1)

	if period:
		raw = get_stock_data(ticker, period=period)
		start_datetime, end_datetime = get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
		raw = get_stock_data(ticker, start_datetime=start_datetime, end_datetime=end_datetime)
	else:
		return {}, 400

	data = process_stock_data(raw, interval)
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	data['start_date'], data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	return json.dumps(data)


@bp.route('/api/get_stock_close_pct', methods=['GET'])
def api_get_stock_close_pct():
	ticker = request.args.get('ticker', type=str, default='0005-HK').upper().replace(".", "-")
	start_epoch = request.args.get("start_epoch", type=int)
	end_epoch = request.args.get("end_epoch", type=int)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int, default=1)

	if period:
		raw = get_stock_data(ticker, period=period)
		start_datetime, end_datetime = get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
		raw = get_stock_data(ticker, start_datetime, end_datetime)
	else:
		return {}, 400

	data = process_stock_data(raw, interval, include=['close_pct'])
	data['ticker'], data['period'], data['interval'] = ticker, period, interval
	data['start_date'], data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	return json.dumps(data)


@bp.route('/api/get_industry_close_pct', methods=['GET'])
def api_get_industry_close_pct():
	industry = request.args.get('industry', type=str, default='Banks')
	start_epoch = request.args.get("start_epoch", type=int)
	end_epoch = request.args.get("end_epoch", type=int)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int, default=1)

	if period:
		raw = get_industry_close_pct(industry, period=period)
		start_datetime, end_datetime = get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
		raw = get_industry_close_pct(industry, start_datetime=start_datetime, end_datetime=end_datetime)
	else:
		return {}, 400
	
	data = process_industry_avg(raw, interval)
	data['industry'], data['period'], data['interval'] = industry, period, interval
	data['start_date'], data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	return json.dumps(data)