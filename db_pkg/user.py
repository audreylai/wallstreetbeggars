import pymongo
from . import stock, rules

client = pymongo.MongoClient("mongodb+srv://root:test1234@wallstreetbeggars.auo5igi.mongodb.net/?retryWrites=true&w=majority")
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
	cursor = col_users.find_one({"username": username}, {"_id": 0, "watchlist": 1})['watchlist']
	return list(cursor)


def add_watchlist(username, ticker):
	col_users.update_one({"username": username}, {"$addToSet": { "watchlist": ticker }})


def delete_watchlist(username, ticker):
	col_users.update_one({"username": username}, {"$pull": { "watchlist": ticker }})


def get_watchlist_data(username):
	period = 60
	watchlist_tickers = get_watchlist_tickers(username)
	result = []
	for ticker in watchlist_tickers:
		info = stock.get_stock_info(ticker)
		if info is None: continue
		result.append({
			"ticker": ticker,
			"name": info["name"],
			"price" : stock.get_last_stock_data(ticker)["close"],
			"change": stock.get_stock_data_chartjs(ticker, period=period, precision=2)['last_close_pct'],
			"mkt_cap": info['mkt_cap'],
			"last_si": rules.get_ticker_last_si(ticker)
		})
	return {"table": result, "last_updated": info["last_updated"]}