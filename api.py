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
	period = request.args.get("period", type=int, default=60)
	interval = request.args.get("interval", type=int, default=1)

	if not ticker_exists(ticker):
		return {}, 400

	data = get_stock_data_chartjs(ticker, period, interval)
	return json.dumps(data)


@bp.route('/api/get_stock_close_pct', methods=['GET'])
def api_get_stock_close_pct():
	ticker = request.args.get('ticker', type=str, default='0005-HK').upper().replace(".", "-")
	period = request.args.get("period", type=int, default=60)
	interval = request.args.get("interval", type=int, default=1)

	if not ticker_exists(ticker):
		return {}, 400

	data = get_stock_data_chartjs(ticker, period, interval)
	return json.dumps(data)


@bp.route('/api/get_industry_tickers_accum_close_pct', methods=['GET'])
def api_get_stock_historical_si():
	industry = request.args.get('industry', type=str, default='Banks')
	period = request.args.get("period", type=int, default=60)

	if not industry_exists(industry): return {}, 400

	data = get_industry_tickers_accum_close_pct_chartjs(industry, period)
	return json.dumps(data)


@bp.route('/api/get_industry_close_pct', methods=['GET'])
def api_get_industry_close_pct():
	industry = request.args.get('industry', type=str, default='Banks')
	period = request.args.get("period", type=int, default=60)
	interval = request.args.get("interval", type=int, default=1)

	if not industry_exists(industry): return {}, 400
	
	data = get_industry_accum_avg_close_pct_chartjs(industry, period, interval)
	return json.dumps(data)