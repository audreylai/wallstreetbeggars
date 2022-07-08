from datetime import *
from queue import Queue
from threading import Thread

import pandas as pd
import pymongo
import requests
import talib as ta
import yfinance as yf
from bs4 import BeautifulSoup

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_users = db["users"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]

def thread_yfinance_info(ticker_list):
	ticker_q = Queue()

	for ticker in ticker_list:
		ticker_q.put(ticker.replace("-", "."))

	tickers = yf.Tickers(' '.join(list(ticker_q.queue)))

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
		'shortName', 'longName', 'exchangeTimezoneName', 'quoteType', 'logo_url',
		"previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"
	]
	df = pd.DataFrame(columns=[convert_name(i) for i in attrs], index=ticker_list)
	df.index.name = 'ticker'

	def get_info():
		while True:
			ticker_name = ticker_q.get()

			res = []
			info = tickers.tickers[ticker_name].info

			for attr in attrs:
				try:
					res.append(info[attr])
				except:
					res.append(None)
					
			df.loc[ticker_name.replace('.', '-')] = res
			print(ticker_name)

			ticker_q.task_done()


	NUM_THREADS = 500
	for t in range(NUM_THREADS):
		worker = Thread(target=get_info)
		worker.daemon = True
		worker.start()
	
	ticker_q.join()

	return df


def add_stock_data_batch():
	col_stock_data.drop({})
	for i in range(1, 250):
		ticker = "%04d-HK" % i
		print(ticker)
		add_stock_data_one(ticker, ticker_type="stock")

	for i in ["^HSI", "^HSCE", "^HSCC"]:
		print(i)
		add_stock_data_one(i, ticker_type="index")


# Web Scraping Code (etnet)
def etnet_scraping():
	def _int(num_str):
		num_str = num_str.replace(',', '')
		if num_str == '': return float('nan')
		if num_str[-1] in 'KMB':
			unit_map = {'K': 10**3, 'M': 10**6, 'B': 10**9}
			num = num_str[:-1]
			unit = num_str[-1]
			return round(float(num) * unit_map.get(unit), 5)
		else:
			return float(num_str)

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
				data = row_data[col].get_text()
				res.append(_int(data))

			scrape_list.append([ticker, industry, *res])

	df = pd.DataFrame(scrape_list, columns=["ticker", "industry", "nominal", "turnover", "mkt_cap", "pct_yield", "pe_ratio"])
	df = df.sort_values("ticker").reset_index(drop=True)
	return df


def add_stock_info_batch(limit=100):
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
	df = df.drop(df[df.ticker >= limit].index)
	
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
	yfinance_df = thread_yfinance_info(ticker_list)
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
	
	# volume moving average
	df["vol_sma20"] = ta.SMA(df.volume, timeperiod=20)

	# rsi + macd
	df["rsi"] = ta.RSI(df.close, timeperiod=14)
	df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df.close, fastperiod=12, slowperiod=26, signalperiod=9)

	# pct change
	# df['close_pct'] = df['close'].pct_change()

	df.dropna(inplace=True)
	if len(df) < 2:
		return

	now = datetime.now()
	if now - df.date.iloc[-1] > timedelta(days=7):
		return

	# convert df to dict
	out = df.to_dict("records")

	# upsert
	col_stock_data.delete_one({'ticker': ticker})
	col_stock_data.insert_one({
		'ticker': ticker,
		'data': out,
		'type': ticker_type,
		'last_close_pct': (df.close.iloc[-1] - df.close.iloc[-2]) / df.close.iloc[-2]
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

	ticker_list = list(map(lambda x: x.replace('-', '.'), ticker_list)) # yfinance takes . in ticker format

	attrs = [
		'sector', 'country', 'website', 'industry', 'currentPrice', 'totalCash',
		'totalDebt', 'totalRevenue', 'totalCashPerShare', 'financialCurrency',
		'shortName', 'longName', 'exchangeTimezoneName', 'quoteType', 'logo_url',
		"previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"
	]
	df = pd.DataFrame(columns=[convert_name(i) for i in attrs], index=ticker_list)
	df.index.name = 'ticker'

	tickers = yf.Tickers(' '.join(ticker_list))

	for ticker_name in ticker_list:
		print(ticker_name)
		res = []
		info = tickers.tickers[ticker_name].info
		try:
			for attr in attrs:
				res.append(info[attr])
			df.loc[ticker_name.replace('.', '-')] = res
		except:
			pass

	df.reset_index(inplace=True)
	return df


def scmp_scraping(limit=10):
	page = requests.get("https://www.scmp.com/topics/hong-kong-stock-market")
	soup = BeautifulSoup(page.content, "html.parser")
	rows = list(soup.find_all("div", attrs={"class": "article-level"}))

	out = []
	for i in range(11, 12+limit):
		try:
			row = rows[i]
			title_tag = row.find('a')

			out.append({
				'title': title_tag.get_text().strip(),
				'link': 'https://www.scmp.com' + title_tag['href'],
				'time': row.find_all('span', attrs={'class': 'author__status-left-time'})[0].get_text()
			})
		except:
			continue

	return out

def ticker_news_scraping(ticker):
	page = requests.get(f"https://www.etnet.com.hk/www/eng/stocks/realtime/quote.php?code={'0' + ticker[:4]}", headers={
		'Referer': f'https://www.etnet.com.hk/www/eng/stocks/realtime/quote.php?code={"0" + ticker[:4]}',
		'Sec-Fetch-Site': 'same-origin'
	})
	soup = BeautifulSoup(page.content, "html.parser")
	rows = soup.find_all("div", attrs={"class": "DivArticleList"})

	out = []
	for row in rows:
		if row.find('span') is None: break
		out.append({
			'title': row.find('a').get_text(),
			'link': "https://www.etnet.com.hk/www/eng/stocks/" + row.find('a')['href'],
			'time': row.find('span').get_text()
		})
	
	return out


def thread_add_stock_data_batch(limit=100):
	col_stock_data.delete_many({})

	ticker_str = ''
	ticker_list = []

	for i in range(1, limit):
		ticker = "%04d-HK" % i
		ticker_str += ticker + ' '
		ticker_list.append(ticker)

	index_list = ['^HSCC', '^HSCE', '^HSI']
	for index in index_list:
		ticker_str += index + ' '
		ticker_list.append(index)

	ticker_str = ticker_str[:-1]
	big_df = yf.download(tickers=ticker_str.replace('-', '.'), period='max', threads=limit, group_by='ticker')

	for ticker in ticker_list:
		df = big_df[ticker.replace('-', '.')].copy()
		ticker_type = 'index' if ticker[0] == '^' else 'stock'

		df.sort_index(inplace=True)
		df.reset_index(inplace=True)
		df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
		pd.to_datetime(df.date)

		df.dropna(inplace=True)
		if df.empty: continue

		for period in [10, 20, 50, 100, 250]:
			df["sma" + str(period)] = ta.SMA(df.close, timeperiod=period)
		
		df["vol_sma20"] = ta.SMA(df.volume, timeperiod=20)
		df["rsi"] = ta.RSI(df.close, timeperiod=14)
		df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df.close, fastperiod=12, slowperiod=26, signalperiod=9)

		# pct change: df['close_pct'] = df['close'].pct_change()

		df.dropna(inplace=True)
		if len(df) < 2: continue

		now = datetime.now()
		if now - df.date.iloc[-1] > timedelta(days=7): continue

		out = df.to_dict("records")
		col_stock_data.insert_one({
			'ticker': ticker,
			'data': out,
			'type': ticker_type,
			'last_close_pct': (df.close.iloc[-1] - df.close.iloc[-2]) / df.close.iloc[-2]
		})
		print(ticker)