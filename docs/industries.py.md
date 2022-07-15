# industries.py
## Table of contents
### utility functions
- `industry_exists()` - Checks if industry exists
- `get_all_industries()` - Returns a list of all industry names


### one industry: close pct / last close pct / accum close pct
- `get_industry_avg_close_pct()` - Returns the average close pct of tickers in an industry per trading day
- `get_industry_accum_avg_close_pct()` - Returns the accumulated average close pct of tickers in an industry per trading day
- `get_industry_avg_last_close_pct()` - Returns the average last close pct of tickers in an industry
- `get_industry_tickers_last_close_pct()` - Returns the last close pct of tickers in an industry


### all industries: close pct / last close pct / accum close pct
- `get_all_industries_avg_close_pct()` - Returns the average close pct of stocks per industry per trading day
- `get_all_industries_avg_last_close_pct()` - Returns the average last close pct of stocks per industry
- `get_all_industries_accum_avg_close_pct()` - Returns the accumulated average close pct of stocks per industry per trading day


### gainers/losers
- `get_leading_industry()` - Returns the leading industry by average last close pct
- `get_industry_tickers_gainers_losers()` - Returns the gainer and loser tickers in an industry
- `get_industry_perf_distribution()` - Returns the performance distribution of tickers in an industry
- `get_industries_gainers_losers_table()` - Returns the gainer and loser industries with additional information


### chartjs functions
- `get_industry_accum_avg_close_pct_chartjs()` - Returns chartjs-formatted average close pct of tickers in an industry per trading day
- `get_all_industries_accum_avg_close_pct_chartjs()` - Returns chartjs-formatted accumulated average close pct of stocks per industry per trading day
- `get_all_industries_avg_last_close_pct_chartjs()` - Returns chartjs-formatted average last close pct of stocks per industry


---
### `industry_exists(industry)`
Params:
* industry (`str`)

Returns: `bool`

Example:
```
>>> industry_exists("Banks")
True

>>> industry_exists("foo")
False
```

---
### `get_all_industries()`
Params: None

Returns: `List`

Example:
```
>>> get_all_industries()
['Agricultural Products',
 'Automobiles',
 'Banks',
...
 'Telecommunication Services',
 'Transportation',
 'Utilities']
```

---
### `get_industry_avg_close_pct(industry, period)`
Params:
* industry (`str`)
* period (`int`): Number of days from today

Returns: `List[Dict]`

Example:
```
>>> get_industry_avg_close_pct("Banks", 60)
[{'close_pct': 0.0005583350472329421,
  'date': datetime.datetime(2022, 5, 16, 0, 0)},
 {'close_pct': 0.0071457625359943044,
  'date': datetime.datetime(2022, 5, 17, 0, 0)},
...
  'date': datetime.datetime(2022, 7, 8, 0, 0)},
 {'close_pct': -0.006953477975907174,
  'date': datetime.datetime(2022, 7, 11, 0, 0)},
 {'close_pct': -0.001862154106347047,
  'date': datetime.datetime(2022, 7, 12, 0, 0)}]
```

---
### `get_industry_accum_avg_close_pct(industry, period)`
Params:
* industry (`str`)
* period (`int`): Number of days from today

Returns: `List[Dict]`

Example:
```
>>> get_industry_accum_avg_close_pct("Banks", 60)
[{'close_pct': 0.007412046859171212,
  'date': datetime.datetime(2022, 5, 17, 0, 0)},
 {'close_pct': -0.00028401225662665064,
  'date': datetime.datetime(2022, 5, 18, 0, 0)},
...
  'date': datetime.datetime(2022, 7, 12, 0, 0)},
 {'close_pct': -0.005898245182778927,
  'date': datetime.datetime(2022, 7, 13, 0, 0)},
 {'close_pct': -0.019597111249850325,
  'date': datetime.datetime(2022, 7, 14, 0, 0)}]
```

---
### `get_industry_avg_last_close_pct(industry)`
Params:
* industry (`str`)

Returns: `float`

Example:
```
>>> get_industry_avg_last_close_pct("Banks")
-0.019597111249850325
```

---
### `get_industry_tickers_last_close_pct(industry)`
Params:
* industry (`str`)

Returns: `List[Dict]`

Example:
```
>>> get_industry_tickers_last_close_pct("Banks")
[{'close_pct': -0.023465724789903275, 'ticker': '0023-HK'},
 {'close_pct': 0.001019352453379252, 'ticker': '0005-HK'},
 {'close_pct': 0.0022641739755306922, 'ticker': '0011-HK'}]
```

---
### `get_all_industries_avg_close_pct(period)`
Params:
* period (`int`): Number of days from today

Returns: `List[Dict]`

Example:
```
>>> get_all_industries_avg_close_pct(5)
[{'industry': 'Media',
  'data': [{'date': datetime.datetime(2022, 7, 8, 0, 0),
    'close_pct': 0.007142850452539706},
   {'date': datetime.datetime(2022, 7, 11, 0, 0),
    'close_pct': -0.036454027192157346},
   {'date': datetime.datetime(2022, 7, 12, 0, 0),
    'close_pct': 0.014285700905079413}]},
 {'industry': 'Industrials',
  'data': [{'date': datetime.datetime(2022, 7, 8, 0, 0),
    'close_pct': -0.014637573119768337}, ...
   ]},
...
 {'industry': 'Utilities',
  'data': [{'date': datetime.datetime(2022, 7, 8, 0, 0),
    'close_pct': 0.004099622793031221}, ...
   ]}]
```

---
### `get_all_industries_avg_last_close_pct()`
Params: None

Returns: `List[Dict]`

Example:
```
>>> get_all_industries_avg_last_close_pct()
[{'close_pct': -0.13114756100666625, 'industry': 'Jewellery & Watches'},
 {'close_pct': -0.044843050861548606, 'industry': 'Health Care'},
 {'close_pct': -0.015696090946450785, 'industry': 'Transportation'},
...
 {'close_pct': 0.02128314809300898, 'industry': 'Other Financials'},
 {'close_pct': 0.029147331303756907, 'industry': 'Food & Beverages'},
 {'close_pct': 0.11111105745466787,
  'industry': 'Commercial & Professional Services'}]
```

---
### `get_all_industries_accum_avg_close_pct(period)`
Params:
* period (`int`): Number of days from today

Returns: `List[Dict]`

Example:
```
>>> get_all_industries_accum_avg_close_pct(5)
[{'data': [{'accum_close_pct': 0.001605510399257289,
            'date': datetime.datetime(2022, 7, 11, 0, 0)},
           {'accum_close_pct': 0.022807115792808023,
            'date': datetime.datetime(2022, 7, 12, 0, 0)},
           {'accum_close_pct': 0.023689434351059344,
            'date': datetime.datetime(2022, 7, 13, 0, 0)},
           {'accum_close_pct': 0.025720783931725555,
            'date': datetime.datetime(2022, 7, 14, 0, 0)}],
  'industry': 'Textiles & Clothing & Accessories'},
 {'data': [{'accum_close_pct': 0.0022622643223422444,
            'date': datetime.datetime(2022, 7, 11, 0, 0)}, ...],
  'industry': 'Insurance'},
...
 {'data': [{'accum_close_pct': 0.0037530222671805008,
            'date': datetime.datetime(2022, 7, 11, 0, 0)}, ...],
  'industry': 'Telecommunication Services'}]
```

---
### `get_leading_industry()`
Params: None

Returns: `Dict`

Example:
```
>>> get_leading_industry()
{'close_pct': 0.11111105745466787,
 'industry': 'Commercial & Professional Services'}
```

---
### `get_industry_tickers_gainers_losers(industry[, limit])`
Params:
* industry (`str`)
* limit (`int`, default=`5`): No. of results to return

Returns: `Tuple[List, List]`

Example: 
```
>>> get_industry_tickers_gainers_losers("Properties", 3)
([{'close_pct': 0.02459015242116691, 'ticker': '0036-HK'},
  {'close_pct': 0.012987039376318732, 'ticker': '0059-HK'},
  {'close_pct': 0.008695685345193604, 'ticker': '0083-HK'}],
 [{'close_pct': -0.03490761402234188, 'ticker': '0029-HK'},
  {'close_pct': -0.028037466475174244, 'ticker': '0095-HK'},
  {'close_pct': -0.025316506313829312, 'ticker': '0037-HK'}])
```

---
### `get_industry_perf_distribution(industry)`
Params:
* industry (`str`)

Returns: `List[int | None]`

Example:
```
>>> get_industry_perf_distribution("Properties")
[0.0, 0.5238095238095238, 0.09523809523809523, 0.38095238095238093, 0.0]

>>> get_industry_perf_distribution("foo")
[None, None, None, None, None]
```

---
### `get_industries_gainers_losers_table([limit])`
Params:
* limit (`int`, default=`5`): No. of results to return

Returns: `Tuple[Dict, Dict]`

Example:
```
>>> get_industries_gainers_losers_table()
([{'close_pct': 0.11111105745466787,
   'industry': 'Commercial & Professional Services',
   'perf_distribution': [0.0, 0.0, 0.0, 1.0, 0.0],
   'top_ticker': {'close_pct': 0.11111105745466787, 'ticker': '0079-HK'}},
...
  {'close_pct': 0.0166666501098216,
   'industry': 'Software & Services',
   'perf_distribution': [0.0, 0.0, 0.0, 1.0, 0.0],
   'top_ticker': {'close_pct': 0.0166666501098216, 'ticker': '0082-HK'}}],
 [{'bottom_ticker': {'close_pct': -0.13114756100666625, 'ticker': '0084-HK'},
   'close_pct': -0.13114756100666625,
   'industry': 'Jewellery & Watches',
   'perf_distribution': [0.0, 1.0, 0.0, 0.0, 0.0]},
...
  {'bottom_ticker': {'close_pct': -0.023465724789903275, 'ticker': '0023-HK'},
   'close_pct': -0.006727399453664444,
   'industry': 'Banks',
   'perf_distribution': [0.0,
                         0.3333333333333333,
                         0.0,
                         0.6666666666666666,
                         0.0]}])
```

---
### `get_all_industries_accum_avg_close_pct_chartjs(period)`
Params:
* period (`int`)

Returns: `List[Dict]`

Example:
```
>>> get_all_industries_accum_avg_close_pct_chartjs(10)
[{'borderColor': 'rgb(0, 191, 160, 0.7)',
  'borderWidth': 2.5,
  'data': [{'x': 1656950400000, 'y': -0.0254}, ...],
  'fill': False,
  'label': 'Agricultural Products',
  'pointBackgroundColor': 'rgb(0, 191, 160, 0.7)',
  'pointRadius': 2,
  'tension': 0.4},
...
  'label': 'Food & Beverages',
  'pointBackgroundColor': 'rgba(230, 0, 73, 0.7)',
  'pointRadius': 2,
  'tension': 0.4}]
```

---
### `get_all_industries_avg_last_close_pct_chartjs()`
Params: None

Returns: `Dict`

Example:
```
>>> get_all_industries_avg_last_close_pct_chartjs()
{'background_color': ['rgb(244 63 94)',
                      'rgb(244 63 94)',
                      ...
                      'rgb(16 185 129)',
                      'rgb(16 185 129)'],
 'data': [-0.13114756100666625,
          -0.044843050861548606,
          ...
          0.029147331303756907,
          0.11111105745466787],
 'labels': ['Jewellery & Watches',
            'Health Care',
            ...
            'Food & Beverages',
            'Commercial & Professional Services']}
```

---
### `get_industry_accum_avg_close_pct_chartjs(industry, period[, interval, precision])`
Params:
* industry (`str`)
* period (`int`): Number of days from today
* interval (`int`, default=`1`): Interval between trading days
* precision (`int`, default=`4`): No. of decimal places to round to

Returns: `Dict`

Example:
```
>>> get_industry_avg_close_pct_chartjs("Banks", 60)
{'accum_close_pct': [{'x': 1652630400000, 'y': 0.0005583350472329421}, ...],
 'industry': 'Banks',
 'interval': 1,
 'period': 60}
```