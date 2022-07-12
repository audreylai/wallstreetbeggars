import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]


def update_active_tickers(username, tickers):
	col_users.update_one({"username": username}, {'$addToSet': {"active": {"$each": tickers}}})


def delete_active_tickers(username, tickers):
	col_users.update_one({"username": username}, {'$pull': {"active": {"$in": tickers}}})


def get_active_tickers(username):
	return col_users.find_one({"username": username}, {"_id": 0, "active": 1})['active']


def update_user_theme(username, theme):
	col_users.update_one({"username": username}, {"$set": {"dark_mode": True if theme == "dark" else False}}, upsert=False)


def get_user_theme(username):
	return col_users.find_one({"username": username}, {"_id": 0, "dark_mode": 1})["dark_mode"]

def get_watchlist_tickers(username):
	return col_users.find_one({"username": username}, {"_id": 0, "watchlist": 1})['watchlist']

def add_watchlist(username, ticker):
	col_users.update_one({"username": username}, {"$addToSet": { "watchlist": ticker }})

def get_watchlist_data(username):
	period = 60
	watchlist_tickers = get_watchlist_tickers(username)
	result = []
	for ticker in watchlist_tickers:
		raw = get_stock_data(ticker, period=period)
		info = get_stock_info(ticker)
		result.append({"ticker": ticker, "name" : info["name"], "price" : raw[-1]['close'], "change": chartjs_stock_data(raw, precision=2, include=['last_close_pct'])['last_close_pct'], "mkt_cap": info['mkt_cap']})
	return {"table": result, "last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"]}