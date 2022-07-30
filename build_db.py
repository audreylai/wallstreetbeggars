import asyncio
import multiprocessing as mp
import os
import pickle as pkl
import signal
import sys
import traceback
from datetime import *
from timeit import default_timer as timer

import colorama
import numpy as np
import pandas as pd
import pymongo
import requests
import talib as ta
import yfinance as yf
from bs4 import BeautifulSoup

from db_pkg.cache import *
from db_pkg.industries import *
from db_pkg.news import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *

HSI_TICKERS = list(map(lambda x: x + '-HK', [
	"0005", "0011", "0388", "0939", "1299", "1398", "2318", "2388", "2628", "3328", "3988", "0002", "0003",
	"0006", "1038", "0012", "0016", "0017", "0083", "0101", "0688", "0823", "1109", "1113", "1997", "2007", 
	"0001", "0019", "0027", "0066", "0151", "0175", "0267", "0288", "0386", "0669", "0700", "0762", "0857",
	"0883", "0941", "1044", "1088", "1093", "1177", "1928", "2018", "2313", "2319", "2382"
]))

STOCK_INFO_COLS = [
	"sector", "country", "website", "totalCash",
	"totalDebt", "totalRevenue", "totalCashPerShare", "financialCurrency",
	"shortName", "longName", "exchangeTimezoneName", "quoteType", "logo_url",
	"bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"
]

CDL_PATTERNS = ta.get_function_groups()["Pattern Recognition"]

USERS_DB = {
  "username": "test",
  "active": ["%04d-HK" % i for i in range(1, 100)],
  "dark_mode": True,
  "buy": [
	"MA10 ≥ MA20", "MA10 ≥ MA50", "MA20 ≥ MA50", "MA20 ≥ MA100", "MA50 ≥ MA100", "MA50 ≥ MA100", "MA100 ≥ MA250",
	"RSI ≥ 50", "RSI ≥ 60", "RSI ≥ 70", "RSI ≥ 80", "RSI ≥ 90",
	"MACD ≥ 0", "MACD ≥ 0.5", "MACD ≥ 1", "MACD ≥ 1.5", "MACD ≥ 2"
  ],
  "sell": [
	"MA10 ≤ MA20", "MA10 ≤ MA50", "MA20 ≤ MA50", "MA20 ≤ MA100", "MA50 ≤ MA100", "MA50 ≤ MA100", "MA100 ≤ MA250",
	"RSI ≤ 50", "RSI ≤ 40", "RSI ≤ 30", "RSI ≤ 20", "RSI ≤ 10",
	"MACD ≤ 0", "MACD ≤ -0.5", "MACD ≤ -1", "MACD ≤ -1.5", "MACD ≤ -2"
  ],
  "watchlist": ["%04d-HK" % i for i in range(1, 10)],
  "cdl_buy": ["CDLHIGHWAVE", "CDLHIKKAKE"],
  "cdl_sell": ["CDLSPINNINGTOP"]
}


class InvalidDF(Exception): pass
class NoData(Exception): pass
class InactiveTicker(Exception): pass


class LOG_LEVEL():
	DEBUG = 0
	INFO  = 1
	WARN  = 2
	ERROR = 3
	FATAL = 4


def log_msg(msg, level=LOG_LEVEL.DEBUG, lock=None, flush=False) -> None:
	time = datetime.now().strftime("%H:%M:%S.%f")[:-3]

	match level:
		case LOG_LEVEL.DEBUG:
			header = f"{colorama.Fore.BLACK}{colorama.Back.GREEN}DEBUG"
			f_msg = f"{colorama.Fore.GREEN}{colorama.Back.BLACK}{msg}"
		case LOG_LEVEL.INFO:
			header = f"{colorama.Fore.BLACK}{colorama.Back.CYAN}INFO "
			f_msg = f"{colorama.Fore.CYAN}{colorama.Back.BLACK}{msg}"
		case LOG_LEVEL.WARN:
			header = f"{colorama.Fore.BLACK}{colorama.Back.YELLOW}WARN "
			f_msg = f"{colorama.Fore.YELLOW}{colorama.Back.BLACK}{msg}"
		case LOG_LEVEL.ERROR:
			header = f"{colorama.Fore.BLACK}{colorama.Back.RED}ERR! "
			f_msg = f"{colorama.Fore.RED}{colorama.Back.BLACK}{msg}"
		case LOG_LEVEL.FATAL:
			header = f"{colorama.Fore.BLACK}{colorama.Back.LIGHTRED_EX}FATAL"
			f_msg = f"{colorama.Style.BRIGHT}{colorama.Fore.RED}{colorama.Back.BLACK}{msg}"
	
	if lock is not None:
		with lock:
			print(f"{time} - {header}{colorama.Style.RESET_ALL} {f_msg}{colorama.Style.RESET_ALL}", flush=flush)
	else:
		print(f"{time} - {header}{colorama.Style.RESET_ALL} {f_msg}{colorama.Style.RESET_ALL}", flush=flush)


def convert_name(name) -> str:
	out = ''
	prev_isupper = False
	for char in name:
		if not prev_isupper and char.isupper(): out += f'_{char.lower()}'
		else: out += char.lower()

		if char.isupper(): prev_isupper = True
		else: prev_isupper = False
	return out


def init_child(lock_):
	global lock
	lock = lock_
	signal.signal(signal.SIGINT, signal.SIG_IGN)


def suffix_to_int(num_str) -> float:
	num_str = num_str.replace(',', '')
	if len(num_str) == 0: return None
	if num_str[-1] in "KMB":
		unit_map = {"K": 10**3, "M": 10**6, "B": 10**9}
		num, unit = num_str[:-1], num_str[-1]
		return round(float(num) * unit_map.get(unit), 5)
	else:
		return float(num_str)


async def get_hkex_df(limit="ALL") -> pd.DataFrame:
	df = pd.read_excel("https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx", usecols=[0, 1, 2, 4], thousands=',')
	df = df.iloc[2:] # remove first 2 unrelated rows
	df.columns.values[:4] = ["ticker", "name", "category", "board_lot"]
	df[["ticker", "board_lot"]] = df[["ticker", "board_lot"]].apply(pd.to_numeric)

	if limit == "ALL":
		df.drop(df[(df.ticker > 4000) & (df.ticker < 6030)].index, inplace=True)
		df.drop(df[(df.ticker > 6700) & (df.ticker < 6800)].index, inplace=True)
		df.drop(df[df.ticker > 10000].index, inplace=True)
	else:
		df.drop(df[df.ticker >= limit].index, inplace=True)
	
	df.ticker = df.ticker.apply(lambda x: f"{str(x).zfill(4)}-HK")
	df.set_index("ticker", inplace=True)
	return df


async def etnet_scraping() -> pd.DataFrame:
	page = requests.get("https://www.etnet.com.hk/www/eng/stocks/industry_adu.php")
	soup = BeautifulSoup(page.content, "html.parser")
	rows = list(soup.find_all("tr", attrs={"valign": "top"}))
 
	url_dict = {}
	for row in rows:
		tag = row.find("a")
		url = "https://www.etnet.com.hk/www/eng/stocks/" + tag["href"]
		industry = tag.get_text()
		url_dict[industry] = url

	scrape_list = []
	for industry in url_dict:
		detail_page = requests.get(url_dict[industry])
		turtle_soup = BeautifulSoup(detail_page.content, "html.parser")
		even_rows = list(turtle_soup.find_all("tr", attrs={"class": "evenRow"}))
		odd_rows = list(turtle_soup.find_all("tr", attrs={"class": "oddRow"}))
		rows = even_rows + odd_rows

		for row in rows:
			ticker = row.find("a").get_text()[-4:] + "-HK"
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


def mp_get_stock_info(ticker) -> Dict | None:
	if not str(type(sys.stdout)) == "<class 'colorama.ansitowin32.StreamWrapper'>":
		colorama.init()

	client = pymongo.MongoClient("mongodb://localhost:27017")
	db = client["wallstreetbeggars"]
	col_stock_data = db["stock_data"]

	try:
		start = timer()
		tmp = yf.Ticker(ticker.replace("-", "."))
		ticker_info = tmp.info

		out = {}
		for col in STOCK_INFO_COLS:
			out[convert_name(col)] = ticker_info.get(col, None)

		if out["ex_dividend_date"] is not None:
			out["ex_dividend_date"] = datetime.fromtimestamp(out["ex_dividend_date"])

		col_stock_data.update_one({"ticker": ticker}, [
			{"$set": out | {"_state": 1}},
		])
		end = timer()
		log_msg(f"{ticker}{' '*(7-len(ticker))}: success (time elapsed: {'%.3f' % (end - start)}s)", level=LOG_LEVEL.DEBUG, lock=lock)

		return out

	except Exception as e:
		log_msg(f"{ticker}{' '*(7-len(ticker))}: {str(e)}", level=LOG_LEVEL.ERROR, lock=lock)


def mp_calc_stock_data(data):
	ticker, df = data

	if not str(type(sys.stdout)) == "<class 'colorama.ansitowin32.StreamWrapper'>":
		colorama.init()

	client = pymongo.MongoClient("mongodb://localhost:27017")
	db = client["wallstreetbeggars"]
	col_stock_data = db["stock_data"]
	
	try:
		start = timer()
		# if col_stock_data.count_documents({"ticker": ticker, "_state": 2}) != 0: raise Exception("Ticker data already exists")
			
		# preprocess stock data
		df.reset_index(inplace=True)
		df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
		pd.to_datetime(df.date)
		df.dropna(inplace=True)
		if df.empty: raise NoData()

		now, last = datetime.now(), df.date.iloc[-1]
		if now - last > timedelta(days=30): raise InactiveTicker()

		for sma_period in [10, 20, 50, 100, 250]:
			df[f"sma{sma_period}"] = ta.SMA(df.close, timeperiod=sma_period)
		df["vol_sma20"] = ta.SMA(df.volume, timeperiod=20)
		df["rsi"] = ta.RSI(df.close, timeperiod=14)
		df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df.close, fastperiod=12, slowperiod=26, signalperiod=9)
		df["obv"] = ta.OBV(df.close, df.volume)
		df["close_pct"] = df.close.pct_change()
		df["stoch_slowk"], df["stoch_slowd"] = ta.STOCH(df.high, df.low, df.close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
		df["stoch_fastk"], df["stoch_fastd"] = ta.STOCHF(df.high, df.low, df.close, fastk_period=5, fastd_period=3, fastd_matype=0)
		df["bbands_upper"], df["bbands_middle"], df["bbands_lower"] = ta.BBANDS(df.close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)

		df.dropna(inplace=True)
		if df.empty: raise NoData()

		if len(df) < 100: raise InvalidDF()

		# cdl patterns
		for pattern in CDL_PATTERNS:
			df[pattern] = getattr(ta, pattern)(df.open, df.high, df.low, df.close)
		df["cdl_pattern"] = np.zeros(len(df), dtype="int64")
		for ix, row in df.iterrows():
			res = 0
			for pattern in CDL_PATTERNS:
				if row[pattern] != 0:
					res += 2**CDL_PATTERNS.index(pattern)
			df.loc[ix, "cdl_pattern"] = res
		df.drop(columns=CDL_PATTERNS, inplace=True)

		cdl_data = df.to_dict("records")
		col_stock_data.update_one({"ticker": ticker}, [
			{"$set": {
				"cdl_data": cdl_data,
				"last_volume": int(df.volume.iloc[-1]),
				"last_close": float(df.close.iloc[-1]),
				"last_close_pct": float(df.close_pct.iloc[-1]),
				"last_cdl_data": cdl_data[-1],
				"type": "index" if ticker[0] == "^" else "stock",
				"is_hsi_stock": ticker in HSI_TICKERS,
				"_state": 2
			}}
		])

		end = timer()
		log_msg(f"{ticker}{' '*(7-len(ticker))}: success (time elapsed: {'%.3f' % (end - start)}s)", level=LOG_LEVEL.DEBUG, lock=lock)
	
	except NoData:
		log_msg(f"{ticker}{' '*(7-len(ticker))}: abort - no data detected", level=LOG_LEVEL.WARN, lock=lock)

	except InvalidDF:
		log_msg(f"{ticker}{' '*(7-len(ticker))}: abort - invalid data (length: {len(df)})", level=LOG_LEVEL.WARN, lock=lock)
	
	except InactiveTicker:
		log_msg(f"{ticker}{' '*(7-len(ticker))}: abort - inactive ticker (last date: {last})", level=LOG_LEVEL.WARN, lock=lock)

	except Exception as e:
		log_msg(f"{ticker}{' '*(7-len(ticker))}: {str(e)}", level=LOG_LEVEL.ERROR, lock=lock)


async def main():
	confirm = input("Are you sure? (Y/N): ")
	if confirm.upper() != "Y": exit()
  
	colorama.init()
	lock = mp.Lock()

	use_cache = True
	limit = "ALL"
	if not isinstance(limit, int) and limit != "ALL":
		raise Exception(f"limit must be an integer or \"ALL\" (currently \"{str(limit)})\"")

	if use_cache: os.makedirs("./tmp", exist_ok=True)

	# --------------------------------------------------
	# Step 1: 
	# - download hkex list of securities
	# - scrape etnet data
	# --------------------------------------------------
	log_msg("Step 1/6: HKEX list of securities + etnet.com.hk stock information", level=LOG_LEVEL.INFO)
	start = timer()
	
	STOCK_INFO_PATH = f"./tmp/stock_info_{limit}.pickle"
	if use_cache and os.path.exists(STOCK_INFO_PATH):
		log_msg(f"Using cached stock info ({STOCK_INFO_PATH})", level=LOG_LEVEL.WARN)
		stock_info_df = pd.read_pickle(STOCK_INFO_PATH)
	else:
		get_hkex_df_task = asyncio.create_task(get_hkex_df(limit))
		etnet_scraping_task = asyncio.create_task(etnet_scraping())
		
		hkex_df = await get_hkex_df_task
		etnet_df = await etnet_scraping_task
		stock_info_df = hkex_df.join(etnet_df, how="inner")

		if use_cache: stock_info_df.to_pickle(STOCK_INFO_PATH)

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)
	

	# --------------------------------------------------
	# Step 2: 
	# - download yfinance stock data
	# --------------------------------------------------
	log_msg("Step 2/6: yfinance stock data", level=LOG_LEVEL.INFO)
	start = timer()

	STOCK_DATA_PATH = f"./tmp/stock_data_{limit}.pickle"
	STOCK_DATA_INDEX_PATH = f"./tmp/stock_data_index.pickle"

	if use_cache and os.path.exists(STOCK_DATA_PATH):
		log_msg(f"Using cached stock data ({STOCK_DATA_PATH})", level=LOG_LEVEL.WARN)
		all_stock_data_df = pd.read_pickle(STOCK_DATA_PATH)
	else:
		tickers_str = ' '.join(list(stock_info_df.index)).replace('-', '.')
		all_stock_data_df = yf.download(tickers=tickers_str, period="15y", threads=100, group_by="ticker")
		all_stock_data_df.sort_index(inplace=True)

		if use_cache: all_stock_data_df.to_pickle(STOCK_DATA_PATH)

	# index stock data
	if use_cache and os.path.exists(STOCK_DATA_INDEX_PATH):
		log_msg(f"Using cached stock data ({STOCK_DATA_INDEX_PATH})", level=LOG_LEVEL.WARN)
		index_stock_data_df = pd.read_pickle(STOCK_DATA_INDEX_PATH)
	else:
		tickers_str = "^HSI ^HSCC ^HSCE"
		index_stock_data_df = yf.download(tickers=tickers_str, period="15y", threads=3, group_by="ticker")
		index_stock_data_df.sort_index(inplace=True)

		if use_cache: index_stock_data_df.to_pickle(STOCK_DATA_INDEX_PATH)

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)


	# --------------------------------------------------
	# Step 3: 
	# - initialize databases (stock_data, cache, users)
	# --------------------------------------------------
	log_msg("Step 3/6: initialize databases", level=LOG_LEVEL.INFO)
	start = timer()

	client = pymongo.MongoClient("mongodb://localhost:27017")
	db = client["wallstreetbeggars"]
	col_stock_data = db["stock_data"]
	col_cache = db["cache"]
	col_users = db["users"]

	col_stock_data.delete_many({})
	col_cache.delete_many({})
	col_users.delete_many({})

	col_users.insert_one(USERS_DB)

	stock_info_df.reset_index(inplace=True)
	stock_info_df["_state"] = np.zeros(len(stock_info_df), dtype=int)
	col_stock_data.insert_many(stock_info_df.to_dict("records"))
	col_stock_data.insert_many([
		{"ticker": "^HSI", "_state": 1},
		{"ticker": "^HSCC", "_state": 1},
		{"ticker": "^HSCE", "_state": 1}
	])
	del stock_info_df

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)
	

	# --------------------------------------------------
	# Step 4: 
	# - download yfinance stock info
	# - insert into stock data db
	# --------------------------------------------------
	log_msg("Step 4/6: yfinance stock info", level=LOG_LEVEL.INFO)
	start = timer()
	tickers = list(map(lambda x: x.replace('.', '-'), set(all_stock_data_df.columns.get_level_values(0))))

	YF_STOCK_INFO_PATH = f"./tmp/yf_stock_info_{limit}.pickle"
	if use_cache and os.path.exists(YF_STOCK_INFO_PATH):
		log_msg(f"Using cached yfinance stock info ({YF_STOCK_INFO_PATH})", level=LOG_LEVEL.WARN)

		with open(YF_STOCK_INFO_PATH, "rb") as fo:
			data = pkl.load(fo)
			for ticker in tickers:
				col_stock_data.update_one({"ticker": ticker}, [
					{"$set": data[ticker] | {"_state": 1}},
				])

	else:
		THREAD_COUNT = 50
		with mp.Pool(THREAD_COUNT, initializer=init_child, initargs=(lock, )) as pool:
			res = pool.map(mp_get_stock_info, tickers)

		if use_cache:
			out = {}
			
			for ticker, data in zip(tickers, res):
				out[ticker] = data

			with open(YF_STOCK_INFO_PATH, "wb") as fo:
				pkl.dump(out, fo)

	
	cursor = col_stock_data.delete_many({"_state": {"$ne": 1}})
	log_msg(f"Dropped {cursor.deleted_count} documents ({col_stock_data.count_documents({})} remaining)", level=LOG_LEVEL.DEBUG)

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)


	# --------------------------------------------------
	# Step 5: 
	# - validate ticker data
	# - compute candlestick patterns
	# - compute indicators (SMA, RSI, MACD, etc)
	# --------------------------------------------------
	log_msg("Step 5/6: pattern/indicator calculations", level=LOG_LEVEL.INFO)
	start = timer()
	stock_data_dfs = []
	for ticker in tickers:
		stock_data_dfs.append((ticker, all_stock_data_df[ticker.replace('-', '.')]))
	for ticker in ["^HSI", "^HSCC", "^HSCE"]:
		stock_data_dfs.append((ticker, index_stock_data_df[ticker]))
	del all_stock_data_df
	del index_stock_data_df

	THREAD_COUNT = 10
	with mp.Pool(THREAD_COUNT, initializer=init_child, initargs=(lock, )) as pool:
		pool.map(mp_calc_stock_data, stock_data_dfs)

	cursor = col_stock_data.delete_many({"_state": {"$ne": 2}})
	log_msg(f"Dropped {cursor.deleted_count} documents ({col_stock_data.count_documents({})} remaining)", level=LOG_LEVEL.DEBUG)

	now = datetime.now()
	col_stock_data.update_many({}, [
		{"$unset": "_state"},
		{"$set": {"last_updated": now}}
	])

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)


	# --------------------------------------------------
	# Step 6: 
	# - save rules results and historical si data to db
	# --------------------------------------------------
	log_msg("Step 6/6: save rules results + historical si", level=LOG_LEVEL.INFO)
	start = timer()
	if limit == "ALL":
		save_rules_results(progress=False)
		save_historical_si(progress=False)
	else:
		save_rules_results(limit=limit, progress=False)
		save_historical_si(limit=limit, progress=False)
		

	end = timer()
	log_msg(f"Time elapsed: {'%.3f' % (end - start)}s\n", level=LOG_LEVEL.DEBUG)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		sys.exit(0)
	except Exception as e:
		log_msg(traceback.format_exc(), level=LOG_LEVEL.FATAL)
