from datetime import datetime, timedelta

from typing import Dict, List, Tuple
import pymongo
from pprint import pprint
from . import stock, utils

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]
col_testing = db["testing"]

last_trading_date = datetime(2022, 7, 13)


def get_all_industries() -> List:
	return col_testing.distinct("industry")


def get_industry_avg_close_pct(industry, period) -> List[Dict]:
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
	return list(cursor)


def get_industry_avg_close_pct_chartjs(industry, period, interval=1, precision=4) -> Dict:
	data = get_industry_avg_close_pct(industry, period)
	out = {
		"close_pct": [],
		"industry": industry, "period": period, "interval": interval
	}

	for c, row in enumerate(data):
		if c % interval != 0: continue

		epoch_timestamp = int(datetime.timestamp(row['date']) * 1000)

		out["close_pct"].append({
			'x': epoch_timestamp,
			'y': round(row["close_pct"], precision)
		})
	
	return out


def get_all_industries_avg_close_pct(period) -> List[Dict]:
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
	return out

# WARN: this function will break, update last_trading date
def get_all_industries_avg_last_close_pct() -> List[Dict]:
	cursor = col_testing.aggregate([
		{"$match": {"type": "stock"}},
		{"$project": {
			"cdl_data": {
				"$filter": {
					"input": "$cdl_data",
					"as": "cdl_data",
					"cond": {"$and": [
						{"$gte": ["$$cdl_data.date", last_trading_date]},
					]}
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
			'close_pct': pymongo.ASCENDING
		}}
	])

	return list(cursor)
	

def get_top_industry() -> Dict:
	data = get_all_industries_avg_last_close_pct()
	return data[-1]

# WARN: this function will break, update last_trading date
def get_industry_tickers_last_close_pct(industry) -> List[Dict]:
	last_trading_date = datetime(2022, 7, 13)

	cursor = col_testing.aggregate([
		{"$match": {"industry": industry}},
		{"$project": {
			"cdl_data": {
				"$filter": {
					"input": "$cdl_data",
					"as": "cdl_data",
					"cond": {"$and": [
						{"$gte": ["$$cdl_data.date", last_trading_date]},
					]}
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
			'close_pct': pymongo.ASCENDING
		}}
	])

	return list(cursor)

# WARN: this function will break, update last_trading date
def get_industry_gainers_losers(industry, limit=5) -> Tuple[List, List]:
	data = get_industry_tickers_last_close_pct(industry)
	gainers = list(filter(lambda x: x['close_pct'] > 0, data))
	losers = list(filter(lambda x: x['close_pct'] < 0, data))

	return gainers[::-1][:min(len(gainers), limit):], losers[:min(len(losers), limit)]

# TODO: rewrite this hot garbage
def process_gainers_losers_industry(gainers, losers):
	out = {
		'gainers': [],
		'losers': []
	}

	industry_details = {}

	for industry in losers:
		industry_stocks_last_close_pct = get_industry_stocks(industry[0], 60, stock_params=["last_close_pct"])
		industry_stocks_last_close_pct = sorted(industry_stocks_last_close_pct.items(), key=lambda kv: kv[1]['last_close_pct'])
		industry_stocks_last_close_pct = [[i[0], i[1]['last_close_pct']] for i in industry_stocks_last_close_pct]
		top_ticker, top_ticker_change = industry_stocks_last_close_pct[0]

		perf_distribution = [0 for _ in range(5)]
		for ticker, change in industry_stocks_last_close_pct:
			if change > 2: perf_distribution[4] += 1
			elif change > 0: perf_distribution[3] += 1
			elif change == 0: perf_distribution[2] += 1
			elif change > -2: perf_distribution[1] += 1
			else: perf_distribution[0] += 1
		perf_distribution = list(map(lambda x: (x/sum(perf_distribution))*100, perf_distribution))

		out["losers"].append({
			"industry": industry[0],
			"change": industry[1],
			"top_ticker":  top_ticker,
			"top_ticker_change": top_ticker_change,
			"perf_distribution": perf_distribution
		})
		industry_details[industry[0]] = industry_stocks_last_close_pct

	for industry in gainers:
		industry_stocks_last_close_pct = get_industry_stocks(industry[0], 60, stock_params=["last_close_pct"])
		industry_stocks_last_close_pct = sorted(industry_stocks_last_close_pct.items(), key=lambda kv: kv[1]['last_close_pct'], reverse=True)
		industry_stocks_last_close_pct = [[i[0], i[1]['last_close_pct']] for i in industry_stocks_last_close_pct]
		top_ticker, top_ticker_change = industry_stocks_last_close_pct[0]

		perf_distribution = [0 for _ in range(5)]
		for ticker, change in industry_stocks_last_close_pct:
			if change > 2: perf_distribution[4] += 1
			elif change > 0: perf_distribution[3] += 1
			elif change == 0: perf_distribution[2] += 1
			elif change > -2: perf_distribution[1] += 1
			else: perf_distribution[0] += 1
		perf_distribution = list(map(lambda x: (x/sum(perf_distribution))*100, perf_distribution))

		out["gainers"].append({
			"industry": industry[0],
			"change": industry[1],
			"top_ticker":  top_ticker,
			"top_ticker_change": top_ticker_change,
			"perf_distribution": perf_distribution
		})
		industry_details[industry[0]] = industry_stocks_last_close_pct
	
	return out, industry_details

# TODO: replace this hot garbage with a chartjs fn
def get_all_industries_close_pct(period=None, limit=9):
	all_industry_cmp = []

	industry_list = get_all_industries()

	alpha = 0.7
	color_list = [
		f"rgba(230, 0, 73, {alpha})", f"rgba(11, 180, 255, {alpha})", f"rgba(80, 233, 145, {alpha})",
		f"rgba(230, 216, 0, {alpha})", f"rgba(155, 25, 245, {alpha})", f"rgba(255, 163, 0, {alpha})",
		f"rgba(220, 10, 180, {alpha})", f"rgba(179, 212, 255, {alpha})", f"rgb(0, 191, 160, {alpha})"
	]
	
	all_industry_last_cmp_raw = []
	all_industry_last_cmp = []

	color_index = 0
	for industry in industry_list:
		data = get_industry_avg_close_pct_chartjs(industry, period=period)['close_pct']
		color = color_list[color_index % len(color_list)]
		color_index += 1
		all_industry_cmp.append({
			'label': industry,
			'data': data,
			'borderColor': color,
			'fill': False,
			'borderWidth': 2.5,
			'tension': 0.4,
			'pointBackgroundColor': color, 
			'pointRadius': 2,
		})
		
		if len(data) > 2:
			last_pct_change = (data[-1]['y'] - data[-2]['y']) / (1 + data[-2]['y'])
			all_industry_last_cmp_raw.append([industry, last_pct_change])

	all_industry_last_cmp_raw = sorted(all_industry_last_cmp_raw, key=lambda x: x[1])
	all_industry_last_cmp = {
		'labels': [i[0] for i in all_industry_last_cmp_raw],
		'data': [i[1]*100 for i in all_industry_last_cmp_raw],
		'background_color': ['rgb(244, 63, 94)' if i[1] < 0 else 'rgb(16, 185, 129)' for i in all_industry_last_cmp_raw]
	}
	return all_industry_cmp[:limit], all_industry_last_cmp