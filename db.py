from datetime import *
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import pymongo
import json
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import requests

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]

# Upserts --------------------
def add_stock_data_one(ticker):
	df = yf.download(ticker.replace('-', '.'), period="10y", progress=False)
	if df.empty:
		return
	
	# format columns
	df.reset_index(inplace=True)

	df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
	pd.to_datetime(df.date)

	# moving averages
	for period in [10, 20, 50, 100, 250]:
		df["sma" + str(period)] = ta.SMA(df.close, timeperiod=period)

	# rsi + macd
	df["rsi"] = ta.RSI(df.close, timeperiod=14)
	df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df.close, fastperiod=12, slowperiod=26, signalperiod=9)

	df.dropna(inplace=True)

	# convert df to dict for upsert
	out = df.to_dict("records")

	# upsert
	query = {ticker: {"$exists": True}}
	col_stock_data.delete_one(query)
	col_stock_data.insert_one({ticker: out})


def add_stock_data_batch():
	col_stock_data.drop({})
	for i in range(1, 100):
		ticker = "%04d-HK" % i
		print(ticker)
		add_stock_data_one(ticker)

def add_hsi_data():
    hsilist = ["^HSI", "^HSCE", "^HSCC", "^HSIL"]
    for i in hsilist:
        print(i)
        add_stock_data_one(i)

# Web Scraping Code (etnet)
def etnet_scraping():
	page = requests.get("https://www.etnet.com.hk/www/eng/stocks/industry_adu.php")
	soup = BeautifulSoup(page.content, "html.parser")
	# Fetch the table row with the link
	rows = list(soup.find_all("tr", attrs={"valign": "top"}))
	url_dict = {}
	for row in rows:
		# Fetch the <a> with the link + industry name
		tag = row.find("a")
		url = "https://www.etnet.com.hk/www/eng/stocks/" + tag["href"] # Gets value of attribute
		industry = tag.get_text()
		url_dict[industry] = url

	scrape_list = []
	for industry in url_dict:
		detail_page = requests.get(url_dict[industry])
		turtle_soup = BeautifulSoup(detail_page.content, "html.parser")
		
		# combine rows
		even_rows = list(turtle_soup.find_all("tr", attrs={"class": "evenRow"}))
		odd_rows = list(turtle_soup.find_all("tr", attrs={"class": "oddRow"}))
		rows = even_rows + odd_rows

		for row in rows:
			ticker = row.find("a").get_text()[-4:] + "-HK"
			res = []
			row_data = list(row.find_all("td", attrs={"align": "right"}))
			for col in [1, 3, 4, 5, 6]: # nominal, turnover, mkt_cap, pct_yield, pe_ratio
				res.append(row_data[col].get_text())
				if col == 6 and res[-1] == '': # pe_ratio
					res[-1] = 'N/A'

			scrape_list.append([ticker, industry, *res])

	df = pd.DataFrame(scrape_list, columns=["ticker", "industry", "nominal", "turnover", "mkt_cap", "pct_yield", "pe_ratio"])
	df = df.sort_values("ticker").reset_index(drop=True)
	return df


def add_stock_info_batch():
	# drop existing data
	col_stock_info.delete_many({})
	df = pd.read_excel('https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=[0, 1, 2, 4], thousands=',')

	# last update date
	last_updated = datetime.strptime(df.iloc[0, 0].split()[3], "%d/%m/%Y")
	col_stock_info.insert_one({"last_updated": last_updated})

	# preprocessing
	df = df.iloc[2:] # remove first 2 unrelated rows
	df.columns.values[:4] = ['ticker', 'name', 'category', 'board_lot']
	df[['ticker', 'board_lot']] = df[['ticker', 'board_lot']].apply(pd.to_numeric)

	# drop unrelated rows
	# df = df.drop(df[(df.ticker > 4000) & (df.ticker < 6030)].index)
	# df = df.drop(df[(df.ticker > 6700) & (df.ticker < 6800)].index)
	# df = df.drop(df[df.ticker > 10000].index)
	df = df.drop(df[df.ticker > 100].index)
	
	# convert ticker format
	ticker_list = []
	for ticker in df.ticker:
		ticker_list.append(f"0000{str(ticker)}"[-4:] + "-HK")
	df.ticker = ticker_list

	# etnet web scraping
	scrape_df = etnet_scraping()
	df = pd.merge(df, scrape_df, on="ticker", how="left") # merge dfs by comparing tickers
	df = df.reset_index(drop=True)

	# yfinance info
	yfinance_df = yfinance_info(ticker_list)
	df = pd.merge(df, yfinance_df, on="ticker", how="left") # merge dfs by comparing tickers
	df = df.reset_index(drop=True)
	
	col_stock_info.insert_many(list(df.to_dict('index').values()))


# Functions for Fetching Data from DB -------------------
def get_stock_data(ticker, period):
	# Calculate start date for fetching
	period = int(period)
	startDate = date.today() + relativedelta(days=-period)
	startDateTime = datetime(startDate.year, startDate.month, startDate.day)
	
	# Fetch and return data
	aggInput = "$" + ticker
	out = col_stock_data.aggregate([
		{
			"$project": {
				ticker: {
					"$filter": {
						"input": aggInput,
						"as": "data",
						"cond": {"$and": [
							{"$gte": ["$$data.date", startDateTime]}
						]}
					}
				}
			}
		}
	])
	res_list = [i for i in out if i[ticker] is not None][0][ticker]
	return res_list


def get_industries():
	return col_stock_info.distinct("industry_x")

def yfinance_info(ticker_list):
	def convert_name(name):
		out = ''
		for char in name:
			if char.isupper():
				out += f'_{char.lower()}'
			else:
				out += char
		return out

	attrs = [
		'sector', 'country', 'website', 'industry', 'currentPrice', 'totalCash',
		'totalDebt', 'totalRevenue', 'totalCashPerShare', 'financialCurrency',
		'shortName', 'longName', 'exchangeTimezoneName', 'quoteType', 'logo_url'
	]
	df = pd.DataFrame(columns=[convert_name(i) for i in attrs], index=ticker_list)
	df.index.name = 'ticker'

	for ticker in ticker_list:
		print(ticker)
		res = []
		try:
			info = yf.Ticker(ticker.replace('-', '.')).info # yfinance takes . in ticker format
			for attr in attrs:
				res.append(info[attr])

			df.loc[ticker] = res
		except:
			pass

	df.reset_index(inplace=True)
	return df


def get_stock_info(ticker):
	if ticker == "ALL":
		return {
			"table": col_stock_info.find({"last_updated": {"$exists": False}}, {"_id": 0, "ticker": 1, "name": 1, "board_lot": 1, "industry": 1}),
			"last_updated": col_stock_info.find_one({"last_updated": {"$exists": True}})["last_updated"],
			"industries": get_industries()
		}
	else:
		return col_stock_info.find_one({"ticker": ticker}, {"_id": 0})

# Not actually DB code --------------------
def get_industry_close_pct(industry, period):
	industry_ticker_list = []
	for i in col_stock_info.find({"industry_x": industry}):
		industry_ticker_list.append(i["ticker"])

	out = {}
	for ticker in industry_ticker_list:
		startDate = date.today() + relativedelta(days=-period)
		startDateTime = datetime(startDate.year, startDate.month, startDate.day)
		aggInput = "$" + ticker

		try:
			cursor = col_stock_data.aggregate([
				{
					"$project": {
						ticker: {
							"$filter": {
								"input": aggInput,
								"as": "data",
								"cond": {"$and": [
									{"$gte": ["$$data.date", startDateTime]}
								]}
							}
						}
					}
				}
			])
		
			initial_close = None

			for dic in [i for i in cursor if i[ticker] is not None][0][ticker]:
				if initial_close is None:
					initial_close = dic["close"]

				if dic["date"] in out:
					out[dic["date"]].append((dic["close"] - initial_close) / initial_close)
				else:
					out[dic["date"]] = [(dic["close"] - initial_close) / initial_close]
 
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
