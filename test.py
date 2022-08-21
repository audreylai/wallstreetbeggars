from datetime import *
from timeit import default_timer as timer

from db_pkg.cache import *
from db_pkg.industries import *
from db_pkg.scrape import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *


def test():
	return get_stock_info("0005-HK")

pprint(test())

start = timer()
test()
end = timer()

print(f"Time elapsed: {round(end - start, 3)}s\n")