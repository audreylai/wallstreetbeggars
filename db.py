from datetime import *
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import pymongo
import json
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import requests

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_stock_data = db["stock_data"]
col_stock_info = db["stock_info"]


def add_stock_data():
    pass


def add_stock_info():
    pass


def get_stock_data(ticker, period):
    ticker = ticker.upper()
    period = int(period)
    # startDate = date_validation(ticker, period)
    startDate = date.today() + relativedelta(days=-period)
    startDateTime = datetime(startDate.year, startDate.month, startDate.day)
    aggInput = "$" + ticker
    out = col_stock_data.aggregate([
        {
            "$project": {
                ticker: {
                    "$filter": {
                        "input": aggInput,
                        "as": "data",
                        "cond": {"$and": [
                            {"$gte": ["$$data.Date", startDateTime]}
                        ]}
                    }
                }
            }
        }
    ])
    res_list = [i for i in out if i[ticker] is not None][0][ticker]
    return res_list