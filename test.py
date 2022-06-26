from db import *
from db_utils import *
from utils import *
from pprint import pprint

add_stock_data_batch()
# data = get_last_stock_data('0005-HK')
# parsed_buy_rules, parsed_sell_rules = parse_rules(["MA10 ≤ MA20", "MA20 ≤ MA50", "RSI ≤ 30"], ["MA10 ≥ MA20", "MA20 ≥ MA50", "RSI ≥ 70"])
# hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = format_rules(*get_hit_miss_rules(data, parsed_buy_rules, parsed_sell_rules))
add_stock_info_batch()
# pprint(get_stock_data('0005-HK', 180))
# print(get_all_tickers(ticker_type='index'))
# print(get_industry_close_pct('Health Care', 180))
# print(get_datetime_from_period(180))
# print(ticker_exists('0005-HK'))
# add_rule("test", "sell", "RSI > 30")