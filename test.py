from db import *
from db_utils import *
from utils import *
from pprint import pprint

from queue import Queue
from threading import Thread
import time

# col_thread = db["stock_thread"]
# NUM_THREADS = 1500

# ticker_q = Queue()
# ticker_list = []

# col_thread.drop({})

# for ticker in range(1, 2000):
# 	ticker_q.put(f"0000{str(ticker)}"[-4:] + ".HK")

# tickers = yf.Tickers(' '.join(list(ticker_q.queue)))

# def get_info():
# 	while True:
# 		ticker_name = ticker_q.get()
# 		# with open(f"./{ticker_name}.json", 'w') as f:
# 		# 	json.dump(tickers.tickers[ticker_name].info, f)
# 		col_thread.replace_one({'ticker':ticker_name.replace(".", "-")}, tickers.tickers[ticker_name].info | {"ticker":ticker_name}, upsert=True)
# 		ticker_q.task_done()


# for t in range(NUM_THREADS):
# 	worker = Thread(target=get_info)
# 	worker.daemon = True
# 	worker.start()

# ticker_q.join()
# print('It took', time.time()-start, 'seconds.')


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
	df = df.drop(df[df.ticker > 11].index)
	
	# convert ticker format
	ticker_list = []
	for ticker in df.ticker:
		ticker_list.append(f"0000{str(ticker)}"[-4:] + "-HK")
	df.ticker = ticker_list

	# etnet web scraping
	scrape_df = etnet_scraping()
	df = pd.merge(df, scrape_df, on="ticker", how="left") # merge dfs by comparing tickers
	df = df.reset_index(drop=True)

	col_stock_info.insert_many(list(df.to_dict('index').values()))

	col_thread = db["stock_thread"]
	NUM_THREADS = 500

	ticker_q = Queue()
	ticker_list = []


	for ticker in range(1, 100):
		ticker_q.put(f"0000{str(ticker)}"[-4:] + ".HK")

	tickers = yf.Tickers(' '.join(list(ticker_q.queue)))

	def get_info():
		while True:
			ticker_name = ticker_q.get()
			col_stock_info.replace_one({'ticker':ticker_name.replace(".", "-")}, tickers.tickers[ticker_name].info | {"ticker":ticker_name.replace(".", "-")}, upsert=True)
			ticker_q.task_done()


	for t in range(NUM_THREADS):
		worker = Thread(target=get_info)
		worker.daemon = True
		worker.start()

	ticker_q.join()
	
start = time.time()
add_stock_info_batch()
print('It took', time.time()-start, 'seconds.')
