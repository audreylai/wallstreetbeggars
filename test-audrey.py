from db_pkg.stock import *

print(col_stock_data.count_documents({"is_hsi_stock": True}))