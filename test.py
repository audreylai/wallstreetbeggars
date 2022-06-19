from db import *
from db_utils import *
from utils import *
from pprint import pprint

# add_stock_data_batch()
# add_stock_info_batch()
# pprint(get_stock_data('0005-HK', 180))
# print(get_all_tickers(ticker_type='index'))
# print(get_industry_close_pct('Health Care', 180))
# print(get_datetime_from_period(180))
# print(ticker_exists('0005-HK'))
add_rule("test", "sell", "RSI > 30")