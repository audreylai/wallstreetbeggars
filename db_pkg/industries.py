from datetime import datetime, timedelta

from typing import Dict, List, Tuple
import pymongo
from pprint import pprint
from . import stock, utils, cache

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_testing = db["testing"]

last_trading_date = datetime(2022, 7, 14)


def industry_exists(industry) -> bool:
	res = col_testing.count_documents({"industry": industry})
	return res != 0


def get_all_industries() -> List:
	return col_testing.distinct("industry")


def get_industry_avg_close_pct(industry, period, use_cache=True) -> List[Dict]:
	if not industry_exists(industry): return []

	if use_cache:
		cache_res = cache.get_cached_result("get_industry_avg_close_pct", {"industry": industry, "period": period})
		if cache_res is not None:
			return cache_res

	start_datetime, end_datetime = utils.get_datetime_from_period(period)

	cursor = col_testing.aggregate([
		{"$match": {"industry": industry}},
		{"$unwind": "$cdl_data"},
		{"$match": {
			"$and": [
				{"cdl_data.date": {"$gte": start_datetime}},
				{"cdl_data.date": {"$lte": end_datetime}}
			]
		}},
		{"$group": {
			"_id": "$cdl_data.date",
			"close_pct": {"$avg": "$cdl_data.close_pct"}
		}},
		{"$project": {
			"_id": 0,
			"date": "$_id",
			"close_pct": 1
		}},
		{"$sort": {
			"date": pymongo.ASCENDING
		}}
	])

	out = list(cursor)
	cache.store_cached_result("get_industry_avg_close_pct", {"industry": industry, "period": period}, out)
	return out


def get_industry_accum_avg_close_pct_chartjs(industry, period, interval=1, precision=4) -> Dict:
	data = get_industry_accum_avg_close_pct(industry, period)
	out = {
		"accum_close_pct": [],
		"industry": industry, "period": period, "interval": interval
	}

	for c, row in enumerate(data):
		if c % interval != 0: continue

		epoch_timestamp = int(datetime.timestamp(row["date"]) * 1000)

		out["accum_close_pct"].append({
			'x': epoch_timestamp,
			'y': round(row["accum_close_pct"], precision)
		})
	
	return out

# WARN: this function will break, update last_trading date
def get_industry_avg_last_close_pct(industry) -> float:
	if not industry_exists(industry): return None

	cursor = col_testing.aggregate([
		{"$match": {"industry": industry}},
		{"$unwind": "$cdl_data"},
		{"$match": {
			"cdl_data.date": {"$gte": last_trading_date}
		}},
		{"$group": {
			"_id": "$industry",
			"close_pct": {"$avg": "$cdl_data.close_pct"}
		}},
		{"$project": {
			"_id": 0
		}}
	])
	return cursor.next()["close_pct"]


def get_all_industries_avg_close_pct(period, use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("get_all_industries_avg_close_pct", {"period": period})
		if cache_res is not None:
			return cache_res

	start_datetime, end_datetime = utils.get_datetime_from_period(period)

	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {
			"cdl_data": {
				"$filter": {
					"input": "$cdl_data",
					"as": "cdl_data",
					"cond": {"$and": [
						{"$gte": ["$$cdl_data.date", start_datetime]},
						{"$lte": ["$$cdl_data.date", end_datetime]}
					]}
				}
			},
			"industry": 1,
			"_id": 0
		}},
		{"$unwind": "$cdl_data"},
		{"$project": {
			"industry": 1,
			"date": "$cdl_data.date",
			"close_pct": "$cdl_data.close_pct"
		}},
		{"$group": {
			"_id": {
				"industry": "$industry",
				"date": "$date"	
			},
			"close_pct": {"$avg": "$close_pct"}
		}},
		{"$project": {
			"_id": 0,
			"date": "$_id.date",
			"industry": "$_id.industry",
			"close_pct": 1
		}},
		{"$sort": {
			"date": pymongo.ASCENDING
		}},
		{"$group": {
			"_id": "$industry",
			"date": {"$push": "$date"},
			"close_pct": {"$push": "$close_pct"}
		}},
		{"$project": {
			"_id": 0,
			"industry": "$_id",
			"date": 1,
			"close_pct": 1
		}}
	])

	data = list(cursor)
	out = []
	for row in data:
		out.append({
			"industry": row["industry"],
			"data": [{
				"date": date,
				"close_pct": close_pct
			} for date, close_pct in zip(row["date"], row["close_pct"])]
		})
	
	cache.store_cached_result("get_all_industries_avg_close_pct", {"period": period}, out)
	return out

# WARN: this function will break, update last_trading date
def get_all_industries_avg_last_close_pct(use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("get_all_industries_avg_last_close_pct", {})
		if cache_res is not None:
			return cache_res

	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {
			"cdl_data": {
				"$filter": {
					"input": "$cdl_data",
					"as": "cdl_data",
					"cond": {
						"$gte": ["$$cdl_data.date", last_trading_date]
					}
				}
			},
			"industry": 1,
			"_id": 0
		}},
		{"$unwind": "$cdl_data"},
		{"$project": {
			"industry": 1,
			"close_pct": "$cdl_data.close_pct"
		}},
		{"$group": {
			"_id": "$industry",
			"close_pct": {"$avg": "$close_pct"}
		}},
		{"$project": {
			"_id": 0,
			"industry": "$_id",
			"close_pct": 1
		}},
		{"$sort": {
			"close_pct": pymongo.ASCENDING
		}}
	])

	out = list(cursor)
	cache.store_cached_result("get_all_industries_avg_last_close_pct", {}, out)
	return out
	

def get_leading_industry() -> Dict:
	data = get_all_industries_avg_last_close_pct()
	return data[-1]

# WARN: this function will break, update last_trading date
def get_industry_tickers_last_close_pct(industry, use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("get_industry_tickers_last_close_pct", {"industry": industry})
		if cache_res is not None:
			return cache_res

	cursor = col_testing.aggregate([
		{"$match": {"industry": industry}},
		{"$project": {
			"cdl_data": {
				"$filter": {
					"input": "$cdl_data",
					"as": "cdl_data",
					"cond": {
						"$gte": ["$$cdl_data.date", last_trading_date]
					}
				}
			},
			"ticker": 1,
			"close_pct": 1,
			"_id": 0
		}},
		{"$unwind": "$cdl_data"},
		{"$project": {
			"ticker": 1,
			"close_pct": "$cdl_data.close_pct"
		}},
		{"$sort": {
			"close_pct": pymongo.ASCENDING
		}}
	])

	out = list(cursor)
	cache.store_cached_result("get_industry_tickers_last_close_pct", {"industry": industry}, out)
	return out

# WARN: this function will break, update last_trading date
def get_industry_tickers_gainers_losers(industry, limit=5) -> Tuple[List, List]:
	data = get_industry_tickers_last_close_pct(industry)
	gainers = list(filter(lambda x: x["close_pct"] > 0, data))
	losers = list(filter(lambda x: x["close_pct"] < 0, data))

	return gainers[::-1][:min(len(gainers), limit)], losers[:min(len(losers), limit)]

# WARN: this function will break, update last_trading date
def get_industry_perf_distribution(industry) -> List[int | None]:
	if not industry_exists(industry): return [None for _ in range(5)]

	data = get_industry_tickers_last_close_pct(industry)
	out = [0, 0, 0, 0, 0] # <=-2, -2~0, 0, 0~2, >=2

	for row in data:
		if row["close_pct"] <= -2:
			out[0] += 1
		elif row["close_pct"] < 0:
			out[1] += 1
		elif row["close_pct"] == 0:
			out[2] += 1
		elif row["close_pct"] < 2:
			out[3] += 1
		else:
			out[4] += 1
	
	out = [i/len(data) if len(data) != 0 else None for i in out] # convert to pct
	return out

# WARN: this function will break, update last_trading date
def get_industries_gainers_losers_table(limit=5) -> Tuple[Dict, Dict]:
	data = get_all_industries_avg_last_close_pct()
	gainers = list(filter(lambda x: x["close_pct"] > 0, data))
	losers = list(filter(lambda x: x["close_pct"] < 0, data))
	gainers = gainers[::-1][:min(len(gainers), limit)]
	losers = losers[:min(len(losers), limit)]

	for i in range(len(gainers)):
		industry = gainers[i]["industry"]
		top_ticker, _ = get_industry_tickers_gainers_losers(industry, limit=1)
		top_ticker = top_ticker[0]
		gainers[i]["top_ticker"] = top_ticker
		gainers[i]["perf_distribution"] = get_industry_perf_distribution(industry)
	
	for i in range(len(losers)):
		industry = losers[i]["industry"]
		_, bottom_ticker = get_industry_tickers_gainers_losers(industry, limit=1)
		bottom_ticker = bottom_ticker[0]
		losers[i]["bottom_ticker"] = bottom_ticker
		losers[i]["perf_distribution"] = get_industry_perf_distribution(industry)

	return gainers, losers


def get_all_industries_accum_avg_close_pct_chartjs(period) -> List[Dict]:
	alpha = 0.7
	color_list = [
		f"rgba(230, 0, 73, {alpha})", f"rgba(11, 180, 255, {alpha})", f"rgba(80, 233, 145, {alpha})",
		f"rgba(230, 216, 0, {alpha})", f"rgba(155, 25, 245, {alpha})", f"rgba(255, 163, 0, {alpha})",
		f"rgba(220, 10, 180, {alpha})", f"rgba(179, 212, 255, {alpha})", f"rgb(0, 191, 160, {alpha})"
	]
	industry_list = get_all_industries()[:9]

	out = []
	for industry in industry_list:
		color = color_list.pop()
		out.append({
			"label": industry,
			"data": get_industry_accum_avg_close_pct_chartjs(industry, period)["accum_close_pct"],
			"borderColor": color,
			"pointBackgroundColor": color,
			"fill": False,
			"borderWidth": 2.5,
			"tension": 0.4,
			"pointRadius": 2
		})
	return out

# WARN: this function will break, update last_trading date
def get_all_industries_avg_last_close_pct_chartjs() -> Dict:
	data = get_all_industries_avg_last_close_pct()

	return {
		"labels": [row["industry"] for row in data],
		"data": [row["close_pct"] for row in data],
		"background_color": ["rgb(16 185 129)" if row["close_pct"] > 0 else "rgb(244 63 94)" for row in data]
	}


def get_industry_accum_avg_close_pct(industry, period) -> List[Dict]:
	data = get_industry_avg_close_pct(industry, period)

	accum_close_pct = 0
	out = []
	for i in range(len(data)):
		accum_close_pct += data[i]["close_pct"]
		out.append({
			"date": data[i]["date"],
			"accum_close_pct": accum_close_pct
		})
	return out


def get_all_industries_accum_avg_close_pct(period) -> List[Dict]:
	data = get_all_industries_avg_close_pct(period)
	out = []

	for row in data:
		industry = row["industry"]
		industry_data = row["data"]

		accum_close_pct = 0
		tmp = []
		for i in range(len(industry_data)):
			accum_close_pct += industry_data[i]["close_pct"]
			tmp.append({
				"date": industry_data[i]["date"],
				"accum_close_pct": accum_close_pct
			})
		out.append({
			"industry": industry,
			"data": tmp
		})
	return out


# def audrey_needs_help(start_date=datetime(2022, 7, 13)):
# 	cursor = col_testing.aggregate([
# 		{"$match": {"type": "stock"}},
# 		{"$project": {
# 			"cdl_data": {
# 				"$filter": {
# 					"input": "$cdl_data",
# 					"as": "cdl_data",
# 					"cond": {"$or": [
# 						{"$eq": ["$$cdl_data.date", last_trading_date]},
# 						{"$eq": ["$$cdl_data.date", start_date]}
# 					]}
# 				}
# 			},
# 			"industry": 1,
# 			"_id": 0
# 		}},
# 		{"$group": {
# 			"_id": "$industry",
# 			"close": {"$push": "$cdl_data.close"}
# 		}},
# 		{"$unwind": "$close"},
# 		{"$project": {
# 			"industry": 1,
# 			"close": {"$divide": [{"$subtract": [{"$arrayElemAt":["$close", 1]}, {"$arrayElemAt":["$close", 0]}]}, {"$arrayElemAt":["$close", 0]}]}
# 		}},
# 		{"$group": {
# 			"_id": "$_id",
# 			"change": {"$avg": "$close"}
# 		}},
# 		{"$project" : {
# 			"industry": 1,
# 			"change": 1
# 		}}
# 	])
# 	print(list(cursor))