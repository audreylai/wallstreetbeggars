from db import get_stock_data, add_stock_data_batch
from pprint import pprint

pprint(get_stock_data('0005-HK', 60))
add_stock_data_batch()