import json
from flask import request, Blueprint

from db_pkg.industries import *
from db_pkg.news import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *

bp = Blueprint('app', __name__)

@bp.route('/api/get_stock_data', methods=['GET'])
def api_get_stock_data():
	ticker = request.args.get('ticker', type=str, default='0005-HK').upper().replace(".", "-")
	start_epoch = request.args.get("start_epoch", type=int)
	end_epoch = request.args.get("end_epoch", type=int)
	period = request.args.get("period", type=int)
	interval = request.args.get("interval", type=int, default=1)

	if not ticker_exists(ticker):
		return {}, 400

	if period:
		raw = get_stock_data(ticker, period=period)
		start_datetime, end_datetime = utils.get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
		raw = get_stock_data(ticker, start_datetime=start_datetime, end_datetime=end_datetime)
	else:
		return {}, 400

	data = get_stock_data_chartjs(ticker, period)
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

	if not ticker_exists(ticker):
		return {}, 400

	if period:
		raw = get_stock_data(ticker, period=period)
		start_datetime, end_datetime = utils.get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
	else:
		return {}, 400

	data = get_stock_data_chartjs(ticker, period)
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
		start_datetime, end_datetime = utils.get_datetime_from_period(period)
	elif start_epoch and end_epoch:
		start_datetime = datetime.fromtimestamp(start_epoch)
		end_datetime = datetime.fromtimestamp(end_epoch)
	else:
		return {}, 400
	
	data = get_industry_avg_close_pct_chartjs(industry, period)
	data['industry'], data['period'], data['interval'] = industry, period, interval
	data['start_date'], data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	return json.dumps(data)