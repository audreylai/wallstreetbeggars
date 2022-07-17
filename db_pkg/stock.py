from datetime import datetime
from typing import Dict, List, Tuple

import pymongo
import talib as ta

from . import industries, utils, cache

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]
col_rules_results = db["rules_results"]
col_testing = db["testing"]

candle_names = ta.get_function_groups()["Pattern Recognition"]

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
		}}
	])
	data = cursor.next()['cdl_data']
	return data


def get_stock_data_chartjs(ticker, period, interval=1, precision=4) -> Dict | None:
	if not ticker_exists(ticker): return
	data = get_stock_data(ticker, period)
	out = {
		"cdl": [], "close": [], "close_pct": [], "accum_close_pct": [], 
		"last_close": 0, "last_close_pct": 0,
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

	volume_up_color = "rgba(215, 85, 65, 0.4)"
	volume_dn_color = "rgba(80, 160, 115, 0.4)"
	accum_close_pct = 0

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
		
		accum_close_pct += row["close_pct"]
		out["accum_close_pct"].append({
			'x': epoch_timestamp,
			'y': round(accum_close_pct, precision)
		})

		out["max_vol"] = max(row["volume"], out["max_vol"])
		
		if row["open"] > row["close"]:
			out["vol_color"].append(volume_up_color)
		else:
			out["vol_color"].append(volume_dn_color)
	
	out["last_close"] = round(data[-1]["close"], precision)
	out["last_close_pct"] = data[-1]["close_pct"]

	return out


def get_stock_info(ticker) -> Dict | None:
	if not ticker_exists(ticker): return None
	return col_testing.find_one({"ticker": ticker}, {"_id": 0, "cdl_data": 0})


def get_stock_info_all(industry=None, sort_col="ticker", sort_dir=pymongo.ASCENDING, min_mkt_cap=0, cols=[], use_cache=True):
	if use_cache:
		param_dict = {
			"industry": industry,
			"sort_col": sort_col,
			"sort_dir": sort_dir,
			"min_mkt_cap": min_mkt_cap,
			"cols": cols
		}
		cache_res = cache.get_cached_result("get_stock_info_all", param_dict)
		if cache_res is not None:
			return cache_res

	query = {
		"type": "stock",
		"mkt_cap": {"$gte": min_mkt_cap}
	}
	if industry: query["industry"] = industry
	
	cursor = col_testing\
		.find(query, {"_id": 0} | {k: 1 for k in cols})\
		.sort([(sort_col, sort_dir), ("_id", 1)])\
		.allow_disk_use(True)
	
	out = list(cursor)
	cache.store_cached_result("get_stock_info_all", param_dict, out)
	return out


def get_ticker_list(ticker_type=None) -> List:
	if ticker_type is None:
		return col_testing.distinct("ticker")
	else:
		return col_testing.distinct("ticker", {"type": ticker_type})


def get_gainers_losers(limit=5) -> Tuple[List[str], List[str]]:
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


def get_gainers_losers_table(limit=5) -> Tuple[List[Dict], List[Dict]]:
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


def get_hsi_tickers_table() -> List[Dict]:
	attrs = {"last_close": 1, "last_close_pct": 1}
	cursor = col_testing\
		.find({"is_hsi_stock": True}, {"_id": 0, "ticker": 1, **attrs})\
		.sort("ticker", pymongo.ASCENDING)

	return list(cursor)


def get_last_stock_data(ticker) -> Dict | None:
	if not ticker_exists(ticker): return None
	return col_testing.find_one({"ticker": ticker}, {"_id": 0, "last_cdl_data": 1})["last_cdl_data"]


def get_mkt_overview_table(use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("get_mkt_overview_table", {})
		if cache_res is not None:
			return cache_res

	cursor = col_testing\
		.find({"type": "stock"}, {"_id": 0, "ticker": 1, "last_volume": 1, "last_close_pct": 1})\
		.limit(50).sort("last_volume", pymongo.DESCENDING)

	out = list(cursor)
	cache.store_cached_result("get_mkt_overview_table", {}, out)
	return out


def get_leading_index() -> Dict:
	index_list = ["^HSI", "^HSCC", "^HSCE"]
	res = []

	for index in index_list:
		res.append({
			"index": index,
			"close_pct": get_last_stock_data(index)["close_pct"]
		})
	
	res = sorted(res, key=lambda x: x["close_pct"])
	return res[0]


def get_mkt_direction() -> float:
	return get_last_stock_data("^HSI")["close_pct"]


def get_mkt_momentum(days=10) -> float:
	data = get_stock_data("^HSI", 60)

	# momentum = (V - Vx) / Vx, where V = Latest price, Vx = Closing price x days ago
	V = data[-1]["close"]
	Vx = data[-days]["close"]
	
	return (V - Vx) / Vx

def get_last_cdl_pattern(ticker):
	data = get_last_stock_data(ticker)
	cdl_pattern = data["cdl_pattern"]

	out = []
	for i in range(61):
		if (cdl_pattern & 2**i) >> i:
			out.append(candle_names[i])
	return out

def get_last_updated() -> datetime:
	cursor = col_testing.aggregate([
		{"$match": {"ticker": "^HSI"}},
		{"$project": {"_id": 0, "last_updated": 1}}
	])
	return cursor.next()["last_updated"]