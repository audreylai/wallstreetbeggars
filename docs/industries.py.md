# industries.py
## Table of contents
- `get_all_industries` - Returns a list of all industry names
- `get_industry_avg_close_pct()` - Returns the average close pct of stocks in an industry per trading day
- `get_industry_avg_close_pct_chartjs()` - Returns chartjs-formatted average close pct of stocks in an industry per trading day
- `get_all_industries_avg_close_pct()` - Returns the average close pct of stocks of all industries per trading day

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
### `get_industry_avg_close_pct(ticker, period)`
Params:
* ticker (`str`)
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
### `get_industry_avg_close_pct_chartjs(ticker, period, [interval, precision])`
Params:
* ticker (`str`)
* period (`int`): Number of days from today
* interval (`int`, default=`1`): Interval between trading days
* precision (`int`, default=`4`): No. of decimal places to round to

Returns: `Dict`

Example:
```
>>> get_industry_avg_close_pct_chartjs("Banks", 60)
{'close_pct': [{'x': 1652630400000, 'y': 0.0005583350472329421}, ...],
 'industry': 'Banks',
 'interval': 1,
 'period': 60}
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