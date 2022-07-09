from datetime import datetime
from typing import Dict, List, Tuple

import pymongo

from . import industries, utils

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]
col_rules_results = db["rules_results"]


def ticker_exists(ticker) -> bool:
	res = list(col_stock_data.find({"ticker": ticker}, {"_id": 1}))
	return len(res) != 0


def get_stock_data(ticker, period=None, start_datetime=None, end_datetime=None) -> List[Dict]:
	if period: start_datetime, end_datetime = utils.get_datetime_from_period(period)
	
	cursor = col_stock_data.aggregate([
		{"$match": {"ticker": ticker}},
		{"$project": {
				"_id": 0,
				"data": {
					"$filter": {
						"input": "$data",
						"as": "data",
						"cond": {"$and": [
							{"$gte": ["$$data.date", start_datetime]},
							{"$lte": ["$$data.date", end_datetime]}
						]}
					}
				}
			}
		}
	])
	return cursor.next()['data']


def process_stock_data(data, interval=1, include=[], precision=4, ticker=None, period=None) -> Dict:
	out = {
		'sma10': [], 'sma20': [], 'sma50': [], 'sma100': [], 'sma250': [],
		'macd': [], 'macd_ema': [], 'macd_div': [], 'rsi': [],
		'cdl': [],
		'close': [], 'close_pct': [], 'last_close': 0, 'last_close_pct': 0,
		'volume': [], 'volume_color': [], 'vol_sma20': [], 'max_volume': 0, "first_close": 0
	}
	first_close = None
	
	volume_up_color = 'rgba(215,85,65,0.4)'
	volume_dn_color = 'rgba(80,160,115,0.4)'

	if len(data) == 0:
		return out
	
	for c, i in enumerate(data):
		if c % interval != 0:
			continue

		if i['volume'] > out['max_volume']:
			out['max_volume'] = i['volume']

		if first_close is None:
			first_close = i['close']
			out["first_close"] = first_close

		out['cdl'].append({
			'x': int(datetime.timestamp(i['date']) * 1000),
			'o': round(i['open'], precision),
			'h': round(i['high'], precision),
			'l': round(i['low'], precision),
			'c': round(i['close'], precision)
		})

		for col in ['sma10', 'sma20', 'sma50', 'sma100', 'sma250', 'rsi', 'macd', 'macd_div', 'macd_ema', 'volume', 'vol_sma20', 'close']:
			out[col].append({
				'x': int(datetime.timestamp(i['date']) * 1000),
				'y': round(i[col], precision)
			})

		out['close_pct'].append({
			'x': int(datetime.timestamp(i['date']) * 1000),
			'y': round((i['close'] - first_close) / first_close, precision)
		})

		if i['open'] > i['close']:
			out['volume_color'].append(volume_up_color)
		else:
			out['volume_color'].append(volume_dn_color)

		out['last_close'] = round(i['close'], precision)
	out['last_close_pct'] = round(100 * (out['close'][-1]['y'] - out['close'][-2]['y']) / out['close'][-2]['y'], precision)

	out['interval'] = interval
	out['period'] = period
	out['ticker'] = ticker
	
	if len(include) != 0:
		return dict(filter(lambda k: k[0] in include, out.items()))

	return out


def get_stock_info(ticker, filter_industry="", sort_col="ticker", sort_dir=pymongo.ASCENDING, min_mkt_cap=10**9):
	if ticker == "ALL":
		query = {
			"last_updated": {"$exists": False},
			"mkt_cap": {"$gte": min_mkt_cap}
		}
		if filter_industry != "":
			query["industry_x"] = filter_industry

		return {
			"table": list(
				col_stock_info
				.find(query, {"_id": 0, "ticker": 1, "name": 1, "board_lot": 1, "industry_x": 1, "mkt_cap": 1})
				.sort([(sort_col, sort_dir), ("_id", 1)]) # '_id' to achieve consistent sort results
			),
			"last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"],
			"industries": industries.get_all_industries()
		}
	else:
		return col_stock_info.find_one({"ticker": ticker}, {"_id": 0})


def get_all_tickers(ticker_type=None) -> List:
	if ticker_type is None:
		return col_stock_data.distinct("ticker")
	else:
		return col_stock_data.distinct("ticker", {"type": ticker_type})


def get_gainers_losers(limit=5) -> Tuple[List, List]:
	cursor = col_stock_data.aggregate([
		{"$sort": {"last_close_pct": pymongo.DESCENDING}},
		{"$limit": limit}
	])
	gainers = [i['ticker'] for i in cursor]

	cursor = col_stock_data.aggregate([
		{"$sort": {"last_close_pct": pymongo.ASCENDING}},
		{"$limit": 5
		}
	])
	losers = [i['ticker'] for i in cursor]

	return gainers, losers


def process_gainers_losers(gainers, losers) -> Dict:
	out = {
		'gainers': [],
		'losers': []
	}

	for ticker in gainers:
		if get_stock_info(ticker) is None:
			continue
		data = get_last_stock_data(ticker)
		out['gainers'].append({
			'ticker': ticker,
			'price': data['close'],
			'change': data['close_pct'],
			'volume': data['volume'],
			'mkt_cap': get_stock_info(ticker)['mkt_cap']
		})
	
	for ticker in losers:
		if get_stock_info(ticker) is None:
			continue
		data = get_last_stock_data(ticker)
		out['losers'].append({
			'ticker': ticker,
			'price': data['close'],
			'change': data['close_pct'],
			'volume': data['volume'],
			'mkt_cap': get_stock_info(ticker)['mkt_cap']
		})
	
	return out


def get_hsi_tickers_data() -> List:
	out = []

	hsi_tickers = map(lambda x: x + '-HK', [
		'0005', '0011', '0388', '0939', '1299', '1398', '2318', '2388', '2628', '3328', '3988', '0002', '0003', '0006',
		'1038', '0012', '0016', '0017', '0083', '0101', '0688', '0823', '1109', '1113', '1997', '2007', '0001', '0019',
		'0027', '0066', '0151', '0175', '0267', '0288', '0386', '0669', '0700', '0762', '0857', '0883', '0941', '1044',
		'1088', '1093', '1177', '1928', '2018', '2313', '2319', '2382'
	])
	for ticker in hsi_tickers:
		if not ticker_exists(ticker):
			continue
		out.append({
			'ticker': ticker,
			'last_close_pct': get_last_stock_data(ticker)['close_pct']*100
		})

	return out


def get_last_stock_data(ticker) -> Dict:
	cursor = col_stock_data.aggregate([
		{"$match": {"ticker": ticker}},
		{"$unwind": "$data"},
		{"$sort": {"data.date": pymongo.DESCENDING}},
		{"$limit": 1}
	])
	res = cursor.next()

	return {
		**res['data'],
		'close_pct': res['last_close_pct']
	}


def get_mkt_overview_data() -> Tuple[List, List]:
	res = get_stock_info('ALL', sort_col='mkt_cap', sort_dir=pymongo.DESCENDING)['table'][:50]
	data, last_close_pct = [], []
	for i in res:
		try:
			last_close_pct.append(get_last_stock_data(i['ticker'])['close_pct'])
		except:
			continue
		else:
			data.append({
				'ticker': i['ticker'], 
				'mkt_cap': i['mkt_cap']
			})
	return data, last_close_pct
