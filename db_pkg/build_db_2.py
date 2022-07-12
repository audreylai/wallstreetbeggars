from datetime import *
from pprint import pprint
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
col_testing = db["testing"]

ticker_q = Queue()
info_attrs = [
	'sector', 'country', 'website', 'industry', 'currentPrice', 'totalCash',
	'totalDebt', 'totalRevenue', 'totalCashPerShare', 'financialCurrency',
	'shortName', 'longName', 'exchangeTimezoneName', 'quoteType', 'logo_url',
	"previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"
]

all_stock_data_dict = {}
excel_df = None
etnet_df = None

def main():
	global etnet_df
	global excel_df

	print('Step 1/4: Excel data')
	excel_df = pd.read_excel('https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=[0, 1, 2, 4], thousands=',')
	excel_df = excel_df.iloc[2:] # remove first 2 unrelated rows
	excel_df.columns.values[:4] = ['ticker', 'name', 'category', 'board_lot']
	excel_df[['ticker', 'board_lot']] = excel_df[['ticker', 'board_lot']].apply(pd.to_numeric)

	# drop unrelated rows
	# df = df.drop(df[(df.ticker > 4000) & (df.ticker < 6030)].index)
	# df = df.drop(df[(df.ticker > 6700) & (df.ticker < 6800)].index)
	# df = df.drop(df[df.ticker > 10000].index)
	excel_df.drop(excel_df[excel_df.ticker >= 1000].index, inplace=True)

	# convert ticker format
	ticker_list = []
	for ticker in excel_df.ticker:
		ticker_name = f"0000{str(ticker)}"[-4:] + ".HK"
		ticker_list.append(ticker_name)
		ticker_q.put(ticker_name)

	for index in ['^HSI', '^HSCC', '^HSCE']:
		ticker_list.append(index)
		ticker_q.put(index)

	excel_df.ticker = ticker_list[:-3]
	excel_df.set_index('ticker', inplace=True)


	print('Step 2/4: Etnet scraping')
	etnet_df = etnet_scraping()

	
	print('Step 3/4: Download stock data')
	NUM_THREADS = 500
	all_stock_data_df = yf.download(
		tickers=' '.join(ticker_list).replace('-', '.'),
		period="max", threads=NUM_THREADS, group_by="ticker"
	)
	for ticker in ticker_list:
		all_stock_data_dict[ticker.replace('-', '.')] = all_stock_data_df[ticker.replace('-', '.')].copy()


	print('Step 4/4: Stock info + calculations + insert')
	for _ in range(NUM_THREADS):
		worker = Thread(target=insert_data, daemon=True)
		worker.start()
	ticker_q.join()


def convert_name(name):
		out = ''
		prev_isupper = False
		for char in name:
			if not prev_isupper and char.isupper(): out += f'_{char.lower()}'
			else: out += char.lower()

			if char.isupper(): prev_isupper = True
			else: prev_isupper = False
		return out

	
def suffix_to_int(num_str):
		num_str = num_str.replace(',', '')
		if num_str == '': return None
		if num_str[-1] in 'KMB':
			unit_map = {'K': 10**3, 'M': 10**6, 'B': 10**9}
			num = num_str[:-1]
			unit = num_str[-1]
			return round(float(num) * unit_map.get(unit), 5)
		else:
			return float(num_str)


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
			ticker = row.find("a").get_text()[-4:] + ".HK"
			res = []
			row_data = list(row.find_all("td", attrs={"align": "right"}))
			for col in [1, 3, 4, 5, 6]: # nominal, turnover, mkt_cap, pct_yield, pe_ratio
				data = row_data[col].get_text()
				res.append(suffix_to_int(data))

			scrape_list.append([ticker, industry, *res])

	df = pd.DataFrame(scrape_list, columns=["ticker", "industry", "nominal", "turnover", "mkt_cap", "pct_yield", "pe_ratio"])
	df.sort_values("ticker", inplace=True)
	df.set_index("ticker", inplace=True)
	return df


def insert_data():
	while not ticker_q.empty():
		try:
			ticker_name = ticker_q.get()

			# download stock data
			if ticker_name not in all_stock_data_dict: raise Exception('Not found in yfinance stock data')
			df = all_stock_data_dict[ticker_name]

			# download stock info
			ticker_obj = yf.Ticker(ticker_name)
			ticker_info = ticker_obj.info
			
			# preprocess stock data
			df.sort_index(inplace=True)
			df.reset_index(inplace=True)
			df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
			pd.to_datetime(df.date)
			df.dropna(inplace=True)
			if df.empty: raise Exception('Invalid DF')

			# sma
			for sma_period in [10, 20, 50, 100, 250]:
				df[f"sma{sma_period}"] = ta.SMA(df.close, timeperiod=sma_period)

			# vol_sma20, rsi, macd, close_pct
			df["vol_sma20"] = ta.SMA(df.volume, timeperiod=20)
			df["rsi"] = ta.RSI(df.close, timeperiod=14)
			df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df.close, fastperiod=12, slowperiod=26, signalperiod=9)
			df['close_pct'] = df['close'].pct_change()

			# date checking
			df.dropna(inplace=True)
			now, last = datetime.now(), df.date.iloc[-1]
			if df.empty or now - last > timedelta(days=7): raise Exception('Invalid DF')

			cdl_data = df.to_dict("records")

			ticker_type = "index" if ticker_name[0] == "^" else "stock"
			col_testing.delete_many({"ticker": ticker_name.replace('.', '-')})

			if ticker_type == "stock":
				# stock info
				info_dict = {}
				for attr in info_attrs:
					try:
						info_dict[convert_name(attr)] = ticker_info[attr]
					except:
						info_dict[convert_name(attr)] = None

				if info_dict['ex_dividend_date'] is not None:
					info_dict['ex_dividend_date'] = datetime.fromtimestamp(info_dict['ex_dividend_date'])

				# etnet data
				etnet_dict = etnet_df.loc[ticker_name].to_dict()
				
				# insert
				col_testing.insert_one({
					"ticker": ticker_name.replace('.', '-'),
					"type": ticker_type,
					"last_updated": now,
					"cdl_data": cdl_data,
					**info_dict,
					**etnet_dict,
					"last_close_pct": df.close_pct.iloc[-1]
				})
			else:
				# insert
				col_testing.insert_one({
					"ticker": ticker_name.replace('.', '-'),
					"type": ticker_type,
					"last_updated": now,
					"cdl_data": cdl_data,
					"last_close_pct": df.close_pct.iloc[-1]
				})

			print(ticker_name)
		except Exception as e:
			print(f'{ticker_name} - {e}')
		
		ticker_q.task_done()

		
if __name__ == "__main__":
	main()
