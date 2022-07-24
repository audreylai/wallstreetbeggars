
from datetime import *
# # from db_utils import *
# # from utils import *
# from pprint import pprint
# # from threading_test import *
from timeit import default_timer as timer

import colorama
import numpy as np
import pandas as pd
import talib as ta

from db_pkg.cache import *
from db_pkg.industries import *
from db_pkg.news import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *

# candle_names = ta.get_function_groups()["Pattern Recognition"]

def test():
	return save_rules_results(limit=100)

# pprint(test())

start = timer()
test()
end = timer()

print(f"Time elapsed: {round(end - start, 3)}s\n")