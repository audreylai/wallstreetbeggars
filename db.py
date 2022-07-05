from datetime import *
import pymongo
from utils import *

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]


def ticker_exists(ticker):
	res = list(col_stock_data.find({"ticker": ticker}, {"_id": 1})) # only return _id for performance
	return len(res) != 0


def get_gainers_losers():
	cursor = col_stock_data.aggregate([
		{
			"$sort": {"last_close_pct": pymongo.DESCENDING}
		},
		{
			"$limit": 5
		}
	])
	gainers = [i for i in cursor]
	gainers = [i['ticker'] for i in gainers]

	cursor = col_stock_data.aggregate([
		{
			"$sort": {"last_close_pct": pymongo.ASCENDING}
		},
		{
			"$limit": 5
		}
	])
	losers = [i for i in cursor]
	losers = [i['ticker'] for i in losers]

	return gainers, losers


def get_last_stock_data(ticker):
	cursor = col_stock_data.aggregate([
		{
			"$match": {"ticker": ticker}
		},
		{
			"$unwind": "$data"
		},
		{
			"$sort": {"data.date": pymongo.DESCENDING}
		},
		{
			"$limit": 1
		}
	])
	res = [i for i in cursor][0]

	out = res['data']
	out['close_pct'] = res['last_close_pct']
	return out


def get_stock_data(ticker, period=None, start_datetime=None, end_datetime=None):
	if period:
		start_datetime, end_datetime = get_datetime_from_period(period)
	
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
	out = [i for i in cursor][0]['data']
	return out


def get_all_tickers(ticker_type=None):
	if ticker_type is None:
		return col_stock_data.distinct("ticker")
	else:
		return col_stock_data.distinct("ticker", {"type": ticker_type})


def get_all_industries():
	return col_stock_info.distinct("industry_x")


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
			"industries": get_all_industries()
		}
	else:
		return col_stock_info.find_one({"ticker": ticker}, {"_id": 0})


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


def get_industry_close_pct(industry, period=None, start_datetime=None, end_datetime=None):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])

	out = {}
	for c, ticker in enumerate(ticker_list):
		if period:
			start_datetime, end_datetime = get_datetime_from_period(period)

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
					out[i["date"]] = [222 for _ in range(c)]
				else:
					out[i["date"]] = out[j][:-1]

			out[i["date"]].append((i["close"] - initial_close) / initial_close)

		prev = 0.0
		for k, v in out.items():
			if len(out[k]) != c+1:
				out[k].append(prev)
			prev = v[-1]

	return out


def get_industry_stocks(industry, period, stock_params=[]):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])
	
	out = {}
	for ticker in ticker_list:
		if not ticker_exists(ticker): continue
		raw = get_stock_data(ticker, period)
		data = process_stock_data(raw, 1, include=stock_params)
		out[ticker] = data
	
	return out


def process_gainers_losers(gainers, losers):
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

		out["losers"].append({
			"industry": industry[0],
			"change": industry[1],
			"top_ticker":  top_ticker,
			"top_ticker_change": top_ticker_change
		})
		industry_details[industry[0]] = industry_stocks_last_close_pct

	for industry in gainers:
		industry_stocks_last_close_pct = get_industry_stocks(industry[0], 60, stock_params=["last_close_pct"])
		industry_stocks_last_close_pct = sorted(industry_stocks_last_close_pct.items(), key=lambda kv: kv[1]['last_close_pct'], reverse=True)
		industry_stocks_last_close_pct = [[i[0], i[1]['last_close_pct']] for i in industry_stocks_last_close_pct]
		top_ticker, top_ticker_change = industry_stocks_last_close_pct[0]

		out["gainers"].append({
			"industry": industry[0],
			"change": industry[1],
			"top_ticker":  top_ticker,
			"top_ticker_change": top_ticker_change
		})
		industry_details[industry[0]] = industry_stocks_last_close_pct
	
	return out, industry_details


def get_mkt_overview_data():
	res = get_stock_info('ALL', sort_col='mkt_cap', sort_dir=pymongo.DESCENDING)['table'][:40]
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


def get_marquee_data():
	out = []

	hsi_tickers = ['0005', '0011', '0388', '0939', '1299', '1398', '2318', '2388', '2628', '3328', '3988', '0002', '0003', '0006', '1038', '0012', '0016', '0017', '0083', '0101', '0688', '0823', '1109', '1113', '1997', '2007', '0001', '0019', '0027', '0066', '0151', '0175', '0267', '0288', '0386', '0669', '0700', '0762', '0857', '0883', '0941', '1044', '1088', '1093', '1177', '1928', '2018', '2313', '2319', '2382']
	hsi_tickers = map(lambda x: x + '-HK', hsi_tickers)
	for ticker in hsi_tickers:
		if not ticker_exists(ticker):
			continue
		out.append({
			'ticker': ticker,
			'last_close_pct': get_last_stock_data(ticker)['close_pct']*100
		})

	return out


# User
def update_active_tickers(username, tickers):
	col_users.update_one({"username":username}, {'$addToSet': {
		'active': {"$each": tickers}
		}
	})


def delete_active_tickers(username, tickers):
	col_users.update_one({"username":username}, {'$pull': {
		'active': {"$in": tickers}
		}
	})


def get_active_tickers(username):
	return col_users.find_one({"username": username}, {"active": 1})

def get_rules(username):
	return col_users.find_one({"username": username}, {"_id":0, "buy": 1, "sell": 1})

def update_rules(username, buy, sell):
	col_users.update_one({"username": username}, {"$set": {"buy": buy, "sell":sell}}, upsert=False)

def update_user_theme(username, theme):
	col_users.update_one({"username": username}, {"$set": {"dark_mode": True if theme == "dark" else False}}, upsert=False)

def get_user_theme(username):
	return col_users.find_one({"username": username}, {"_id": 0, "dark_mode":1})["dark_mode"]
