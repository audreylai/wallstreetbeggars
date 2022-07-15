import pymongo
from . import user, utils, stock

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_rules_results = db["rules_results"]


def get_rules(username):
	return col_users.find_one({"username": username}, {"_id": 0, "buy": 1, "sell": 1})


def update_rules(username, buy, sell):
	col_users.update_one({"username": username}, {"$set": {"buy": buy, "sell": sell}})


def get_rules_results(ticker):
	cursor = col_rules_results.find({"ticker": ticker}, {"_id": 0, "hit_buy_rules": 1, "hit_sell_rules": 1, "miss_buy_rules": 1, "miss_sell_rules": 1})
	return cursor.next()


def get_watchlist_rules_results(username):
	ticker_list = user.get_watchlist_tickers(username)
	out = {}
	for ticker in ticker_list:
		# print(ticker)
		out[ticker] = get_rules_results(ticker)
	return out


def save_rules_results(limit=100):
	col_rules_results.delete_many({})

	for i in range(limit):
		ticker = "%04d-HK" % i
		if not stock.ticker_exists(ticker): continue
	
		last_stock_data = stock.get_last_stock_data(ticker)
		user_rules = get_rules("test")
		parsed_buy_rules, parsed_sell_rules = utils.parse_rules(user_rules["buy"], user_rules["sell"])
		hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = utils.format_rules(*utils.get_hit_miss_rules(last_stock_data, parsed_buy_rules, parsed_sell_rules))

		col_rules_results.insert_one({
			'ticker': ticker,
			'hit_buy_rules': hit_buy_rules,
			'hit_sell_rules': hit_sell_rules,
			'miss_buy_rules': miss_buy_rules,
			'miss_sell_rules': miss_sell_rules
		})
		
		print(ticker)