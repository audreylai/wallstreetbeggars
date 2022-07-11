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