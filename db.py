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


def get_stock_info(ticker, filter_industry="", sort_col="ticker", sort_dir=pymongo.ASCENDING):
	if ticker == "ALL":
		query = {"last_updated": {"$exists": False}}
		if filter_industry != "":
			query["industry_x"] = filter_industry

		return {
			"table": list(col_stock_info
				.find(query, {"_id": 0, "ticker": 1, "name": 1, "board_lot": 1, "industry_x": 1, "mkt_cap": 1})
				.sort([(sort_col, sort_dir), ("_id", 1)]) # '_id' to achieve consistent sort results
			),
			"last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"],
			"industries": get_all_industries()
		}
	else:
		return col_stock_info.find_one({"ticker": ticker}, {"_id": 0})


def get_industry_close_pct(industry, period=None, start_datetime=None, end_datetime=None):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])

	out = {}
	print(ticker_list)
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
	print(tickers)
	col_users.update_one({"username":username}, {'$pull': {
		'active': {"$in": tickers}
		}
	})


def get_active_tickers(username):
	return col_users.find_one({"username": username}, {"active": 1})


def add_rule(username, rule_type, rule):
	col_users.update_one({"username": username}, {'$addToSet': {
		rule_type: rule
	}})


def delete_rule(username, rule_type, rule):
	col_users.update_one({"username": username}, {'$pull': {
		rule_type: rule
	}})


def edit_rules(username, rule_type, rule, action):
	res = list(col_users.find({"username": username}, {"_id": 0}))
	# Gets list of rules from buy/sell
	rule_list = res[0][rule_type]
	# Edit rule list
	if action == "add":
		rule_list.append(rule)
	elif action == "delete":
		rule_list.remove(rule)
		
	data = {
		rule_type: rule_list
	}
	col_users.update_one({"username": username}, {"$set": data}, upsert=False)