from db_pkg.build_db import *
from db_pkg.user import *
from db_pkg.industries import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.news import *
from db_pkg.cache import *

# # from db_utils import *
# # from utils import *
# from pprint import pprint
# # from threading_test import *
from timeit import default_timer as timer

def test():
	period = 60

	# mkt_overview_data = get_mkt_overview_table()
	# dark_mode = get_user_theme("test")

	chart_data = {
		# "hsi_chartjs": get_stock_data_chartjs("^HSI", period),
		# "hscc_chartjs": get_stock_data_chartjs("^HSCC", period),
		# "hsce_chartjs": get_stock_data_chartjs("^HSCE", period),

		# 'mkt_overview_data': 		[{k: v for k, v in d.items() if k != 'last_close_pct'} for d in mkt_overview_data],
		# 'mkt_overview_last_close_pct': [x["last_close_pct"] for x in mkt_overview_data],
		'all_industry_cmp': get_all_industries_avg_close_pct_chartjs(period),
		'all_industry_last_cmp': get_all_industries_avg_last_close_pct_chartjs()
	}
	
	# card_data = {
	# 	"mkt_momentum": get_mkt_momentum(),
	# 	"mkt_direction": get_mkt_direction(),
	# 	"leading_index": get_leading_index(),
	# 	"leading_industry": get_leading_industry()
	# }

	# gainers_data, losers_data = get_gainers_losers_table()
	# table_data = {
	# 	"gainers": gainers_data,
	# 	"losers": losers_data
	# }
	
	# marquee_data = get_hsi_tickers_table()
	# watchlist_rules_data = get_watchlist_rules_results('test')
	# news = scmp_scraping(5)

# pprint(test())

start = timer()
test()
end = timer()

print(f'{round((end - start)*1000, 3)}ms')

# print(get_watchlist_rules_results('test'))
# pprint(get_all_tickers())
