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

def add_stock_data_batch():
	col_stock_data.drop({})
	for i in range(1, 100):
		ticker = "%04d-HK" % i
		print(ticker)
		add_stock_data_one(ticker, ticker_type="stock")

	for i in ["^HSI", "^HSCE", "^HSCC"]:
		print(i)
		add_stock_data_one(i, ticker_type="index")

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

def add_stock_data_one(ticker, ticker_type=None):
	df = yf.download(ticker.replace('-', '.'), period="max", progress=False)
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

	# convert df to dict
	out = df.to_dict("records")

	# upsert
	col_stock_data.delete_one({'ticker': ticker})
	col_stock_data.insert_one({
		'ticker': ticker,
		'data': out,
		'type': ticker_type
	})

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