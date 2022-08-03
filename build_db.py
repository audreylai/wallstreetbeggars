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
from db_pkg.scrape import *
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
	"active": list(map(lambda x: x + '-HK', [
		"3958", "1286", "2181", "0105", "0622", "0289", "2231", "2163", "1817", "3662", "1569", "1234", "1809", "6198", "0548",
		"0297", "0369", "0877", "0699", "0921", "2343", "6199", "3798", "3836", "9979", "3639", "1432", "1508", "0051", "0686",
		"2678", "1383", "0251", "6178", "0338", "1836", "1778", "6806", "6978", "1578", "0116", "1568", "1600", "1680", "1811",
		"0978", "0035", "0215", "6868", "0579", "3969", "0382", "6889", "1368", "3709", "0028", "3800", "1551", "6820", "1935",
		"0086", "0991", "6865", "1258", "3899", "1119", "3818", "0308", "2232", "1196", "0816", "6968", "1668", "2552", "6958",
		"1271", "3877", "0062", "1224", "2935", "0826", "3996", "0546", "0256", "2233", "2727", "6068", "1515", "1257", "0440",
		"6069", "0189", "1963", "0856", "0806", "0797", "3613", "0337", "1660", "1860", "0530", "3718", "1141", "1905", "1117",
		"6855", "2798", "0934", "0207", "0576", "2038", "1317", "2600", "1052", "0506", "1098", "1357", "1565", "1727", "1898",
		"0737", "1176", "3309", "0581", "0059", "3618", "1608", "2019", "0242", "1521", "1981", "3866", "1381", "1772", "0751",
		"0302", "0120", "0272", "0775", "0460", "1333", "0119", "1777", "1111", "0658", "3698", "2696", "1877", "1031", "2666",
		"1996", "2001", "0691", "0071", "2342", "1675", "1958", "0177", "0142", "2098", "0832", "6139", "0127", "3339", "0357",
		"1302", "2616", "0639", "1992", "1883", "1911", "0855", "0694", "1089", "2299", "1919", "1907", "2356", "3301", "1083",
		"1475", "6100", "0045", "2362", "0590", "1282", "6055", "6049", "3813", "0861", "0412", "0520", "0341", "1212", "2883",
		"1157", "1788", "0376", "9928", "0034", "1171", "1513", "0303", "0777", "0173", "1478", "0799", "1589", "0743", "1137",
		"2500", "3308", "0552", "1186", "9968", "6099", "0665", "3993", "0410", "0363", "9983", "2858", "2607", "2777", "0373",
		"1910", "0358", "1622", "1890", "3377", "0631", "1070", "1337", "3606", "3396", "3898", "3759", "2048", "1686", "1316",
		"1769", "1773", "0179", "1610", "3347", "2103", "6066", "1199", "2768", "0041", "1766", "2380", "0697", "2186", "0902",
		"2005", "9966", "1787", "0696", "0095", "0354", "9909", "9969", "0416", "0489", "1776", "1908", "2016", "0670", "0916",
		"0390", "0819", "2039", "2611", "0570", "1966", "2066", "0763", "6881", "0081", "9996", "3933", "1208", "1765", "1873",
		"2196", "1896", "1387", "2772", "1055", "1477", "1448", "1816", "0043", "3868", "1800", "3669", "0136", "1310", "2400",
		"3633", "1755", "3668", "1628", "0973", "6158", "0165", "2314", "1359", "6185", "0551", "0087", "0336", "2238", "0316",
		"1458", "9990", "1112", "9926", "1717", "1339", "0867", "2799", "0535", "1238", "0604", "2669", "0123", "1252", "6088",
		"6886", "6288", "3883", "1789", "1233", "1818", "1530", "0069", "3998", "3990", "6837", "0636", "6169", "0493", "1638",
		"0753", "1099", "9923", "1585", "0512", "0014", "0200", "6060", "3900", "0659", "9922", "0010", "0152", "1951", "3320",
		"1308", "1995", "6078", "3360", "0148", "1548", "2333", "0257", "0683", "9668", "9997", "0345", "2357", "1882", "2013",
		"2338", "0371", "3331", "0392", "1336", "0220", "3311", "0144", "1888", "0839", "2869", "1060", "2899", "0780", "0053",
		"0522", "0467", "1268", "0728", "1797", "6818", "0754", "1114", "3908", "2359", "0425", "0008", "0019", "1347", "1988",
		"2588", "0293", "0667", "3918", "2282", "2328", "3323", "2689", "1030", "1999", "6030", "3383", "0836", "0168", "0966",
		"1088", "1691", "0004", "2202", "1813", "1378", "2128", "0135", "0247", "0998", "0486", "0023", "3319", "0884", "3808",
		"0857", "0772", "0868", "2601", "6110", "2018", "0880", "3888", "0817", "0586", "0992", "0083", "0151", "3799", "0788",
		"2638", "1658", "0268", "0853", "1821", "0656", "1044", "1801", "0914", "1128", "3380", "1288", "1169", "0270", "1913",
		"1211", "1313", "6823", "0968", "1193", "2331", "0322", "0285", "1066", "1929", "0386", "0006", "6808", "0101", "0288",
		"2688", "1997", "0017", "1038", "0384", "0881", "0813", "1972", "2888", "1833", "1093", "2382", "6186", "2628", "3328",
		"1579", "0012", "6098", "2319", "1918", "1113", "6160", "0291", "0762", "3968", "0175", "1177", "0669", "0002", "0981",
		"0001", "2313", "6969", "0003", "0267", "2007", "3988", "3692", "2020", "0945", "3333", "0011", "2388", "0688", "0708",
		"0066", "0960", "2269", "0241", "0027", "1109", "1928", "6862", "0016", "2378", "1876", "1398", "0883", "0388", "9999",
		"2318", "1810", "0005", "1299", "9618", "0941", "0939", "3690", "0700", "9988"
	])),
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
	"cdl_buy": [
		"CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE", "CDL3OUTSIDE", "CDL3STARSINSOUTH",
		"CDL3WHITESOLDIERS", "CDLABANDONEDBABY", "CDLADVANCEBLOCK", "CDLBELTHOLD", "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU",
		"CDLCONCEALBABYSWALL", "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER", "CDLDOJI", "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING"
	],
	"cdl_sell": [
		"CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE", "CDL3OUTSIDE", "CDL3STARSINSOUTH",
		"CDL3WHITESOLDIERS", "CDLABANDONEDBABY", "CDLADVANCEBLOCK", "CDLBELTHOLD", "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU",
		"CDLCONCEALBABYSWALL", "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER", "CDLDOJI", "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING"
	]
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
	limit = 250
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
