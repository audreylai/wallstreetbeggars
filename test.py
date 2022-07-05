from matplotlib.pyplot import table
from db import *
from db_utils import *
from utils import *
from pprint import pprint

# industries_pct = get_all_industries_close_pct(period=60, limit=None)[1]
# gainers, losers = [], []
# for i in range(len(industries_pct['labels'])):
# 	if industries_pct['data'][i] > 1:
# 		gainers.append((industries_pct['labels'][i], industries_pct['data'][i]))
# 	else:
# 		losers.append((industries_pct['labels'][i], industries_pct['data'][i]))
# table_data = process_gainers_losers_industry(gainers, losers)

# pprint(table_data)

# pprint(get_industry_stocks('Telecommunication Services', period=60, stock_params=['last_close_pct']))

# pprint(process_industry_avg(get_industry_close_pct('Hotels & Restaurants & Leisure', period=60)))
pprint(get_industry_close_pct('Hotels & Restaurants & Leisure', period=60))
# industry_stocks_last_close_pct = get_industry_stocks('Diversified Metals & Minerals', 60, stock_params=["last_close_pct"])
# top_ticker = sorted(industry_stocks_last_close_pct.items(), key=lambda kv: kv[1]['last_close_pct'])
# print(top_ticker)