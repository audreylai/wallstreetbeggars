from datetime import datetime
from typing import List

import pymongo

from . import utils

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]


def get_industry_stocks(industry, period, stock_params=[]):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])
	
	out = {}
	for ticker in ticker_list:
		if not ticker.ticker_exists(ticker): continue
		raw = ticker.get_stock_data(ticker, period)
		data = ticker.process_stock_data(raw, 1, include=stock_params)
		out[ticker] = data
	
	return out


def get_industry_close_pct(industry, period=None, start_datetime=None, end_datetime=None):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])

	out = {}
	for c, ticker in enumerate(ticker_list):
		if period:
			start_datetime, end_datetime = utils.get_datetime_from_period(period)

		cursor = col_stock_data.aggregate([
			{
				"$match": {"ticker": ticker}
			},
			{
				"$project": {
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
		res = [i for i in cursor if i["data"] is not None]
		if len(res) == 0:
			continue
		res = res[0]["data"]

		initial_close = None
		for i in res:
			if initial_close is None:
				initial_close = i["close"]

			if i["date"] not in out:
				prev_date = None
				for j in out.keys():
					if j > i['date']:
						break
					prev_date = j

				if prev_date is None:
					out[i["date"]] = [0 for _ in range(c)]
				else:
					out[i["date"]] = out[j][:-1]

			out[i["date"]].append((i["close"] - initial_close) / initial_close)

		prev = 0.0
		for k, v in out.items():
			if len(out[k]) != c+1:
				out[k].append(prev)
			prev = v[-1]

	return out


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


def get_all_industries() -> List:
	return col_stock_info.distinct("industry_x")

# TODO: rewrite this hot garbage
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
		data = process_industry_avg(get_industry_close_pct(industry, period=period))['close_pct']
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


def process_industry_avg(data, interval=1):
	out = {
		'close_pct': []
	}

	c = -1
	for date, close_pct in data.items():
		c += 1
		if c % interval != 0:
			continue

		out['close_pct'].append({
			'x': datetime.timestamp(date) * 1000, # epoch in milliseconds
			'y': sum(close_pct) / len(close_pct)
		})

	return out
