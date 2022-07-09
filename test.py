from db import *
from db_utils import *
from utils import *
from pprint import pprint
from threading_test import *

# thread_add_stock_data_batch(limit=500)
# add_stock_info_batch(limit=500)
# save_rules_results(limit=500)
pprint(get_watchlist_rules_results('test'))