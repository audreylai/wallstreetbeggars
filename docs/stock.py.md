# stock.py
## Table of contents
- `ticker_exists()` - Checks if ticker exists
- `get_stock_data()` - Returns stock data of a ticker
- `get_stock_data_chartjs()` - Returns chartjs-formatted data of a ticker
- `get_stock_info()` - Returns stock info of a ticker
- `get_stock_info_all()` - Returns stock info of all tickers (with optional sorting)

---
### `ticker_exists(ticker)`
Params:
* ticker (`str`)

Returns: `bool`

Example:
```
>>> ticker_exists("0005-HK")
True

>>> ticker_exists("foo")
False
```

---
### `get_stock_data(ticker, period)`
Params:
* ticker (`str`)
* period (`int`): Number of days from today

Returns: `List[Dict] | None`

Example:
```
>>> get_stock_data("0005-HK", 60)
[{'date': datetime.datetime(2022, 5, 16, 0, 0),
  'open': 47.599998474121094,
  'high': 48.150001525878906,
  'low': 47.5,
  'close': 47.900001525878906,
  'adj_close': 47.900001525878906,
  'volume': 10970715.0,
  'sma10': 48.78000030517578,
  'sma20': 50.45000019073486,
  'sma50': 51.34700004577637,
  'sma100': 52.05950008392334,
  'sma250': 47.65080000305176,
  'vol_sma20': 21034459.75,
  'rsi': 37.78063246003459,
  'macd': -1.3453638729736141,
  'macd_ema': -1.0710464930022545,
  'macd_div': -0.27431737997135963,
  'close_pct': 0.003141393212123589},
 {'date': datetime.datetime(2022, 5, 17, 0, 0),
...
  'macd_div': -0.23733689779942105,
  'close_pct': 0.0030612556301816696}]

>>> get_stock_data("foo", 60)
None
```

---
### `get_stock_data_chartjs(ticker, period, interval, precision)`
Params:
* ticker (`str`)
* period (`int`): Number of days from today
* interval (`int`, default=`1`): Interval between trading days
* precision (`int`, default=`4`): No. of decimal places to round to

Returns: `Dict | None`

Example:
```
>>> get_stock_data_chartjs("0005-HK", 60)
{'cdl': [{'x': 1652630400000, 'o': 47.6, 'h': 48.15, 'l': 47.5, 'c': 47.9}, ...],
 'close': [{'x': 1652630400000, 'y': 47.9}, ...],
 'close_pct': [{'x': 1652630400000, 'y': 0.0031}, ...],
 'last_close': 49.150001525878906,
 'last_close_pct': 0.0030612556301816696,
 'sma10': [{'x': 1652630400000, 'y': 48.78}, ...],
 'sma20': [{'x': 1652630400000, 'y': 50.45}, ...],
 'sma50': [{'x': 1652630400000, 'y': 51.347}, ...],
 'sma100': [{'x': 1652630400000, 'y': 52.0595}, ...],
 'sma250': [{'x': 1652630400000, 'y': 47.6508}, ...],
 'rsi': [{'x': 1652630400000, 'y': 37.7806}, ...],
 'macd': [{'x': 1652630400000, 'y': -1.3454}, ...],
 'macd_ema': [{'x': 1652630400000, 'y': -1.071}, ...],
 'macd_div': [{'x': 1652630400000, 'y': -0.2743}, ...],
 'volume': [{'x': 1652630400000, 'y': 10970715.0}, ...],
 'vol_color': ['rgba(80 160 115 0.4)', ...],
 'vol_sma20': [{'x': 1652630400000, 'y': 21034459.75}, ...],
 'max_vol': 42722173.0,
 'ticker': '0005-HK',
 'period': 60,
 'interval': 1}

>>> get_stock_data_chartjs("foo", 60)
None
```

---
### `get_stock_info(ticker)`
Params:
* ticker (`str`)

Returns: `Dict | None`

Example:
```
>>> get_stock_info("0005-HK", 60)
{'ticker': '0005-HK',
 'type': 'stock',
 'last_updated': datetime.datetime(2022, 7, 12, 14, 44, 36, 290000),
 'sector': 'Financial Services',
 'country': 'United Kingdom',
 'website': 'https://www.hsbc.com',
 'industry': 'Banks',
 'current_price': 49.15,
 'total_cash': 1087012995072,
 'total_debt': 597181005824,
 'total_revenue': 48881000448,
 'total_cash_per_share': 54.286,
 'financial_currency': 'USD',
 'short_name': 'HSBC HOLDINGS',
 'long_name': 'HSBC Holdings plc',
 'exchange_timezone_name': 'Asia/Hong_Kong',
 'quote_type': 'EQUITY',
 'logo_url': 'https://logo.clearbit.com/hsbc.com',
 'previous_close': 49,
 'market_cap': 996762058752,
 'bid': 49.1,
 'ask': 49.15,
 'beta': 0.534259,
 'trailing_pe': 11.170455,
 'trailing_eps': 4.4,
 'dividend_rate': 1.96,
 'ex_dividend_date': datetime.datetime(2022, 3, 10, 8, 0),
 'nominal': 49.1,
 'turnover': 301764000.0,
 'mkt_cap': 999429000000.0,
 'pct_yield': 3.972,
 'pe_ratio': 10.089,
 'name': 'HSBC HOLDINGS',
 'category': 'Equity',
 'board_lot': 400,
 'last_volume': 6152540.0,
 'last_close': 49.150001525878906,
 'last_close_pct': 0.0030612556301816696,
 'last_cdl_data': {'date': datetime.datetime(2022, 7, 12, 0, 0),
  'open': 48.900001525878906,
  'high': 49.349998474121094,
  'low': 48.900001525878906,
  'close': 49.150001525878906,
  'adj_close': 49.150001525878906,
  'volume': 6152540.0,
  'sma10': 50.44500045776367,
  'sma20': 50.4100004196167,
  'sma50': 50.07900024414062,
  'sma100': 51.64250011444092,
  'sma250': 48.07180004882812,
  'vol_sma20': 20612808.1,
  'rsi': 41.340401918484574,
  'macd': -0.2817469577012801,
  'macd_ema': -0.04441005990185907,
  'macd_div': -0.23733689779942105,
  'close_pct': 0.0030612556301816696}}

>>> get_stock_info("foo", 60)
None
```

---
### `get_stock_info_all()`
Params:
* industry (`str`, default=`""`): Filter results by a specific industry
* sort_col (`str`, default=`"ticker"`): Column to perform sorting on
* sort_dir (`int`, default=`pymongo.ASCENDING`): Direction of sorting
* min_mkt_cap (`int`, default=`0`): Filter results by minimum market cap

Returns: `List[Dict]`

Example:
```
>>> get_stock_info_all()
[{'ticker': '0001-HK',
  'type': 'stock',
  'last_updated': datetime.datetime(2022, 7, 12, 14, 44, 35, 674000),
...
   'rsi': 40.34222999414849,
   'macd': -0.0003839934494487343,
   'macd_ema': -0.00015620165490531213,
   'macd_div': -0.0002277917945434222,
   'close_pct': -0.060606070868568396}}]
```