from db_pkg.build_db import *
from db_pkg.user import *
from db_pkg.industries import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.news import *

# from db_utils import *
# from utils import *
# from pprint import pprint
# from threading_test import *
# from timeit import default_timer as timer

thread_add_stock_data_batch(limit=100)
# add_stock_info_batch(limit=100)
save_rules_results(limit=100)

# start = timer()
# get_all_industries_close_pct(period=180)
# get_industry_close_pct('Banks', period=180)
# end = timer()
# print(end - start)

# print(get_watchlist_rules_results('test'))
# pprint(get_all_tickers())
