import pymongo
from . import user, utils, stock

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_rules_results = db["rules_results"]


def get_rules(username):
	return col_users.find_one({"username": username}, {"_id": 0, "buy": 1, "sell": 1, "cdl_buy": 1, "cdl_sell": 1})


def update_rules(username, buy, sell, cdl):
	if cdl:
		col_users.update_one({"username": username}, {"$set": {"cdl_buy": buy, "cdl_sell": sell}})
	else:
		col_users.update_one({"username": username}, {"$set": {"buy": buy, "sell": sell}})


def get_rules_results(ticker, cdl):
	if cdl:
		cursor = col_rules_results.find({"ticker": ticker}, {"_id": 0, "hit_cdl_buy_rules": 1, "hit_cdl_sell_rules": 1, "miss_cdl_buy_rules": 1, "miss_cdl_sell_rules": 1})
	else:
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
		# print(user_rules)

		# Parse regular tech indicator rules
		parsed_buy_rules, parsed_sell_rules = utils.parse_rules(user_rules["buy"], user_rules["sell"])
		hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = utils.format_rules(*utils.get_hit_miss_rules(last_stock_data, parsed_buy_rules, parsed_sell_rules))

		# Check CDL pattern rules
		last_stock_cdl_pattern = stock.get_ticker_last_cdl_pattern(ticker)
		hit_cdl_buy_rules, miss_cdl_buy_rules, hit_cdl_sell_rules, miss_cdl_sell_rules = ([] for i in range(4))
		cdl_buy, cdl_sell = user_rules["cdl_buy"], user_rules["cdl_sell"]
		for pattern in last_stock_cdl_pattern:
			if pattern != None:
				if pattern in cdl_buy:
					hit_cdl_buy_rules.append(pattern)
					cdl_buy.remove(pattern)
				elif pattern in cdl_sell:
					hit_cdl_sell_rules.append(pattern)
					cdl_sell.remove(pattern)
		miss_cdl_buy_rules, miss_cdl_sell_rules = cdl_buy, cdl_sell
			
		col_rules_results.insert_one({
			'ticker': ticker,
			'hit_buy_rules': hit_buy_rules,
			'hit_sell_rules': hit_sell_rules,
			'miss_buy_rules': miss_buy_rules,
			'miss_sell_rules': miss_sell_rules,
			'hit_cdl_buy_rules': hit_cdl_buy_rules,
			'miss_cdl_buy_rules': miss_cdl_buy_rules,
			'hit_cdl_sell_rules': hit_cdl_sell_rules,
			'miss_cdl_sell_rules': miss_cdl_sell_rules
		})
		
		print(ticker)