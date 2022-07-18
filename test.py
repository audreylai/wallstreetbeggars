from csscompressor import compress
from numpy import empty
from db_pkg.build_db import *
from db_pkg.user import *
from db_pkg.industries import *
from db_pkg.rules import *
from db_pkg.utils import *
from db_pkg.stock import *
from db_pkg.news import *
from db_pkg.cache import *
import talib as ta
import pandas as pd
from datetime import *
# # from db_utils import *
# # from utils import *
# from pprint import pprint
# # from threading_test import *
from timeit import default_timer as timer
candle_names = ta.get_function_groups()["Pattern Recognition"]


# def test():
# 	# return clear_all_cache()
# 	return get_all_industries()

# pprint(test())

# start = timer()
# test()
# end = timer()

# print(f'{round((end - start)*1000, 3)}ms')

# print(get_watchlist_rules_results('test'))
# pprint(get_all_tickers())

# def get_industry_accum_avg_close_pct(industry, period) -> List[Dict]:
# 	start_datetime, end_datetime = utils.get_datetime_from_period(period)
# 	accum_close_pct = 0

# 	cursor = col_testing.aggregate([
# 		{"$match": {"industry": industry}},
# 		{"$unwind": "$cdl_data"},
# 		{"$match": {
# 			"$and": [
# 				{"cdl_data.date": {"$gte": start_datetime}},
# 				{"cdl_data.date": {"$lte": end_datetime}}
# 			]
# 		}},
# 		{"$group": {
# 			"_id": "$cdl_data.date",
# 			"close_pct": {"$avg": "$cdl_data.close_pct"}
# 		}},
# 		{"$sort": {
# 			"date": pymongo.ASCENDING
# 		}},
# 		{"$project": {
# 			"_id": 0,
# 			"date": "$_id",
# 			"close_pct": {
# 				"$let": {
# 					"vars": {
# 						"accum_close_pct": {
# 							"$ifNull": [{"$add": ["$$accum_close_pct", "$close_pct"]}, "$close_pct"]
# 						}
# 					},
# 					"in": "$$accum_close_pct"
# 				}
# 			}
# 		}},
# 		{"$sort": {
# 			"date": pymongo.ASCENDING
# 		}}
# 	])
# 	return list(cursor)