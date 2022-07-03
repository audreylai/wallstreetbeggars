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
	out = [i for i in cursor][0]['data']
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


def get_all_industries_close_pct(period=None, start_datetime=None, end_datetime=None):
	all_industry_cmp = []
	industry_list = get_all_industries()[:9]

	alpha = 0.6
	color_list = [
		f"rgba(230, 0, 73, {alpha})", f"rgba(11, 180, 255, {alpha})", f"rgba(80, 233, 145, {alpha})",
		f"rgba(230, 216, 0, {alpha})", f"rgba(155, 25, 245, {alpha})", f"rgba(255, 163, 0, {alpha})",
		f"rgba(220, 10, 180, {alpha})", f"rgba(179, 212, 255, {alpha})", f"rgb(0, 191, 160, {alpha})"
	]
	
	all_industry_last_cmp_raw = []
	all_industry_last_cmp = []

	for industry in industry_list:
		data = process_industry_avg(get_industry_close_pct(industry, period=period))['close_pct']
		color = color_list.pop()

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
		all_industry_last_cmp_raw.append([industry, data[-1]['y']])

	all_industry_last_cmp_raw = sorted(all_industry_last_cmp_raw, key=lambda x: x[1])
	all_industry_last_cmp = {
		'labels': [i[0] if len(i[0]) < 20 else i[0][:17] + '...' for i in all_industry_last_cmp_raw],
		'data': [i[1]*100 for i in all_industry_last_cmp_raw],
		'background_color': ['rgb(244, 63, 94)' if i[1] < 0 else 'rgb(16, 185, 129)' for i in all_industry_last_cmp_raw]
	}

	return all_industry_cmp, all_industry_last_cmp


def get_industry_close_pct(industry, period=None, start_datetime=None, end_datetime=None):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])

	out = {}
	for ticker in ticker_list:
		if period:
			start_datetime, end_datetime = get_datetime_from_period(period)

		try:
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
			res = [i for i in cursor if i["data"] is not None][0]["data"]
			initial_close = None
			for i in res:
				if initial_close is None:
					initial_close = i["close"]

				if i["date"] in out:
					out[i["date"]].append((i["close"] - initial_close) / initial_close)
				else:
					out[i["date"]] = [(i["close"] - initial_close) / initial_close]
 
		except:
			pass

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
