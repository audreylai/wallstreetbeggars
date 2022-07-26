from datetime import *
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


def test():
	clear_all_cache()

# pprint(test())

start = timer()
test()
end = timer()

print(f"Time elapsed: {round(end - start, 3)}s\n")