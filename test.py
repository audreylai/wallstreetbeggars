from db_pkg.build_db import *
from db_pkg.user import *
from db_pkg.industries import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.news import *

# # from db_utils import *
# # from utils import *
# from pprint import pprint
# # from threading_test import *
# from timeit import default_timer as timer

# def test():
# 	return get_all_industries_avg_last_close_pct_chartjs()

# pprint(test())

# start = timer()
# test()
# end = timer()

# print(f'{round((end - start)*1000, 3)}ms')

print(get_industry_tickers_last_close_pct("Banks"))
# print(get_watchlist_rules_results('test'))
# pprint(get_all_tickers())
