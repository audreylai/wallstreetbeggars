
from datetime import *
# # from db_utils import *
# # from utils import *
# from pprint import pprint
# # from threading_test import *
from timeit import default_timer as timer

import colorama
import numpy as np
import pandas as pd
import talib as ta

from db_pkg.cache import *
from db_pkg.industries import *
from db_pkg.news import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *

# candle_names = ta.get_function_groups()["Pattern Recognition"]

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

def test():
	client = pymongo.MongoClient("mongodb://localhost:27017")
	db = client["wallstreetbeggars"]
	col_users = db["users"]

	col_users.delete_many({})
	col_users.insert_one(USERS_DB)
	save_rules_results(limit=100)
	save_historical_si(limit=100, period=180)

# pprint(test())

start = timer()
test()
end = timer()

print(f"Time elapsed: {round(end - start, 3)}s\n")