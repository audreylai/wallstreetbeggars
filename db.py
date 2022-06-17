from datetime import *
from dateutil.relativedelta import relativedelta
import pymongo

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]

# Upserts --------------------



# Functions for Fetching Data from DB -------------------
def get_stock_data(ticker, period):
	# Calculate start date for fetching
	start_date = date.today() + relativedelta(days=-period)
	start_datetime = datetime(start_date.year, start_date.month, start_date.day)
	
	# Fetch and return data
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
							{"$gte": ["$$data.date", start_datetime]}
						]}
					}
				}
			}
		}
	])
	out = [i for i in cursor if i['data'] is not None][0]['data']
	return out

def get_all_tickers(ticker_type=None):
	if ticker_type is None:
		return col_stock_data.distinct("ticker")
	else:
		return col_stock_data.distinct("ticker", {"type": ticker_type})

def get_all_industries():
	return col_stock_info.distinct("industry_x")


def get_stock_info(ticker, sort_col="ticker", sort_dir=pymongo.ASCENDING):
	if ticker == "ALL":
		return {
			"table": list(col_stock_info
				.find({"last_updated": {"$exists": False}}, {"_id": 0, "ticker": 1, "name": 1, "board_lot": 1, "industry_x": 1, "mkt_cap": 1})
				.sort([(sort_col, sort_dir), ("_id", 1)]) # '_id' to achieve consistent sort results
			),
			"last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"],
			"industries": get_all_industries()
		}
	else:
		return col_stock_info.find_one({"ticker": ticker}, {"_id": 0})

# Not actually DB code --------------------
def get_industry_close_pct(industry, period):
	ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		ticker_list.append(i["ticker"])

	out = {}
	print(ticker_list)
	for ticker in ticker_list:
		start_date = date.today() + relativedelta(days=-period)
		start_datetime = datetime(start_date.year, start_date.month, start_date.day)

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
									{"$gte": ["$$data.date", start_datetime]}
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

def process_industry_avg(data, interval):
	out = {
		'close_pct': []
	}

	c = -1
	for date, close_pct in data.items():
		c += 1
		if c % interval != 0:
			continue

		out['close_pct'].append({
			'x': datetime.timestamp(date) * 1000,
			'y': sum(close_pct) / len(close_pct)
		})

	return out


def process_stock_data(data, interval, include=[], precision=4):
	out = {
		'sma10': [],
		'sma20': [],
		'sma50': [],
		'sma100': [],
		'sma250': [],
		'macd': [],
		'macd_ema': [],
		'macd_div': [],
		'rsi': [],
		'cdl': [],
		'close': [],
		'close_pct': [],
		'volume': [],
		'volume_color': [],
		'max_volume': None,
		'last_close': None,
		'last_close_pct': None,
		'date_start': None,
		'date_end': None
	}
	max_volume = 0
	initial_close = None
	
	volume_up_color = 'rgba(215,85,65,0.4)'
	volume_dn_color = 'rgba(80,160,115,0.4)'
	
	for c, i in enumerate(data):
		if c % interval != 0:
			continue

		if i['volume'] > max_volume:
			max_volume = i['volume']

		if initial_close is None:
			initial_close = i['close']

		out['cdl'].append({
			'x': datetime.timestamp(i['date']) * 1000,
			'o': i['open'],
			'h': i['high'],
			'l': i['low'],
			'c': i['close']
		})

		for col in ['sma10', 'sma20', 'sma50', 'sma100', 'sma250', 'rsi', 'macd', 'macd_div', 'macd_ema', 'volume', 'close']:
			out[col].append({
				'x': datetime.timestamp(i['date']) * 1000,
				'y': round(i[col], precision)
			})

		out['close_pct'].append({
			'x': datetime.timestamp(i['date']) * 1000,
			'y': round((i['close'] - initial_close) / initial_close, precision)
		})

		if i['open'] > i['close']:
			out['volume_color'].append(volume_up_color)
		else:
			out['volume_color'].append(volume_dn_color)

		out['last_close'] = round(i['close'], precision)

	out['last_close_pct'] = round(100 * (out['close'][-1]['y'] - out['close'][-2]['y']) / out['close'][-2]['y'], precision)
	out['date_start'] = out['close'][0]['x']
	out['date_end'] = out['close'][-1]['x']

	out['max_volume'] = max_volume

	if len(include) != 0:
		return dict(filter(lambda k: k[0] in include, out.items()))

	return out

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
	if rule_type == "buy":
		col_users.update_one({"username": username}, {'$addToSet': {
		'buy': rule
		}})
	else:
		col_users.update_one({"username": username}, {'$addToSet': {
		'sell': rule
		}})

def delete_rule(username, rule_type, rule):
	if rule_type == "buy":
		col_users.update_one({"username": username}, {'$pull': {
		'buy': rule
		}})
	else:
		col_users.update_one({"username": username}, {'$pull': {
		'sell': rule
		}})