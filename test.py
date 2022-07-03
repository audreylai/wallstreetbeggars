from db import *
from db_utils import *
from utils import *
from pprint import pprint

from queue import Queue
from threading import Thread
import time

start = time.time()

col_thread = db["stock_thread"]
NUM_THREADS = 1500

ticker_q = Queue()
ticker_list = []

col_thread.drop({})

for ticker in range(1, 2000):
	ticker_q.put(f"0000{str(ticker)}"[-4:] + ".HK")

tickers = yf.Tickers(' '.join(list(ticker_q.queue)))

def get_info():
	while True:
		ticker_name = ticker_q.get()
		# with open(f"./{ticker_name}.json", 'w') as f:
		# 	json.dump(tickers.tickers[ticker_name].info, f)
		col_thread.replace_one({'ticker':ticker_name.replace(".", "-")}, tickers.tickers[ticker_name].info | {"ticker":ticker_name}, upsert=True)
		ticker_q.task_done()


for t in range(NUM_THREADS):
	worker = Thread(target=get_info)
	worker.daemon = True
	worker.start()

ticker_q.join()

# add_stock_info_batch()
print('It took', time.time()-start, 'seconds.')
