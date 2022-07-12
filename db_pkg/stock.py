from datetime import datetime
from typing import Dict, List, Tuple
from . import user

import pymongo

from . import industries, utils

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]
col_rules_results = db["rules_results"]

col_testing = db["testing"]


def ticker_exists(ticker) -> bool:
	res = col_testing.count_documents({"ticker": ticker})
	return res != 0


def get_stock_data(ticker, period) -> List[Dict] | None:
	if not ticker_exists(ticker): return
	start_datetime, end_datetime = utils.get_datetime_from_period(period)
	
	cursor = col_testing.aggregate([
		{"$match": {"ticker": ticker}},
		{"$project": {
				"_id": 0,
				"cdl_data": {
					"$filter": {
						"input": "$cdl_data",
						"as": "cdl_data",
						"cond": {"$and": [
							{"$gte": ["$$cdl_data.date", start_datetime]},
							{"$lte": ["$$cdl_data.date", end_datetime]}
						]}
					}
				}
			}
		}
	])
	return cursor.next()['cdl_data']


def get_stock_data_chartjs(ticker, period, interval=1, precision=4) -> Dict | None:
	if not ticker_exists(ticker): return
	data = get_stock_data(ticker, period)

	out = {
		"cdl": [], "close": [], "close_pct": [], "last_close": 0, "last_close_pct": 0,
		"sma10": [], "sma20": [], "sma50": [], "sma100": [], "sma250": [],
		"rsi": [], "macd": [], "macd_ema": [], "macd_div": [],
		"volume": [], "vol_color": [], "vol_sma20": [], "max_vol": 0,
		"ticker": ticker, "period": period, "interval": interval
	}
	attrs = [
		"sma10", "sma20", "sma50", "sma100", "sma250",
		"rsi", "macd", "macd_div", "macd_ema", "volume", "vol_sma20",
		"close", "close_pct"
	]

	volume_up_color = "rgba(215 85 65 0.4)"
	volume_dn_color = "rgba(80 160 115 0.4)"

	for c, row in enumerate(data):
		if c % interval != 0: continue

		epoch_timestamp = int(datetime.timestamp(row['date']) * 1000)

		out["cdl"].append({
			'x': epoch_timestamp,
			'o': round(row["open"], precision),
			'h': round(row["high"], precision),
			'l': round(row["low"], precision),
			'c': round(row["close"], precision)
		})

		for attr in attrs:
			out[attr].append({
				'x': epoch_timestamp,
				'y': round(row[attr], precision)
			})

		out["max_vol"] = max(row["volume"], out["max_vol"])
		
		if row["open"] > row["close"]:
			out["vol_color"].append(volume_up_color)
		else:
			out["vol_color"].append(volume_dn_color)
	
	out["last_close"] = data[-1]["close"]
	out["last_close_pct"] = data[-1]["close_pct"]

	return out


def get_stock_info(ticker) -> Dict:
	return col_testing.find_one({"ticker": ticker}, {"_id": 0, "cdl_data": 0})


def get_stock_info_all(industry="", sort_col="ticker", sort_dir=pymongo.ASCENDING, min_mkt_cap=0):
	query = {
		"mkt_cap": {"$gte": min_mkt_cap}
	}
	if len(filter_industry) != 0: query["industry_x"] = filter_industry
	
	cursor = col_testing\
		.find(query, {"_id": 0, "cdl_data": 0})\
		.sort([(sort_col, sort_dir), ("_id", 1)])
	
	return list(cursor)


def get_ticker_list(ticker_type=None) -> List:
	if ticker_type is None:
		return col_testing.distinct("ticker")
	else:
		return col_testing.distinct("ticker", {"type": ticker_type})


def get_gainers_losers(limit=2) -> Tuple[List, List]:
	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {"_id": 0, "ticker": 1, "last_close_pct": 1}},
		{"$sort": {"last_close_pct": pymongo.DESCENDING}},
		{"$limit": limit}
	])
	gainers = [i["ticker"] for i in cursor]

	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {"_id": 0, "ticker": 1, "last_close_pct": 1}},
		{"$sort": {"last_close_pct": pymongo.ASCENDING}},
		{"$limit": limit}
	])
	losers = [i["ticker"] for i in cursor]
	return gainers, losers


def get_gainers_losers_table(limit=2) -> Tuple[Dict, Dict]:
	attrs = {"last_close": 1, "last_volume": 1, "mkt_cap": 1}

	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {"_id": 0, "ticker": 1, "last_close_pct": 1, **attrs}},
		{"$sort": {"last_close_pct": pymongo.DESCENDING}},
		{"$limit": limit}
	])
	gainers = list(cursor)

	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {"_id": 0, "ticker": 1, "last_close_pct": 1, **attrs}},
		{"$sort": {"last_close_pct": pymongo.ASCENDING}},
		{"$limit": limit}
	])
	losers = list(cursor)
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
	if not ticker_exists(ticker): return

	cursor = col_testing.aggregate([
		{"$match": {"ticker": ticker}},
		{"$unwind": "$cdl_data"},
		{"$sort": {"cdl_data.date": pymongo.DESCENDING}},
		{"$limit": 1}
	])
	res = cursor.next()

	return {
		**res['cdl_data'],
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

def get_watchlist_data(username):
	period = 60
	watchlist_tickers = user.get_watchlist_tickers(username)
	result = []
	for ticker in watchlist_tickers:
		raw = get_stock_data(ticker, period=period)
		info = get_stock_info(ticker)
		result.append({"ticker": ticker, "name" : info["name"], "price" : raw[-1]['close'], "change": chartjs_stock_data(raw, precision=2, include=['last_close_pct'])['last_close_pct'], "mkt_cap": info['mkt_cap']})
	return {"table": result, "last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"]}