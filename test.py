from db import get_stock_data
from pprint import pprint

pprint(get_stock_data('0005-HK', 60))