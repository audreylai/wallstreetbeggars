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
    delete = col_stock_info.delete_many({})

    cols = [0, 1, 2, 4]
    df = pd.read_excel(
        'https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=cols, skiprows=2)
    df = df.rename(columns={'Stock Code': 'stockcode', 'Name of Securities': 'name', 'Category': 'category', 'Board Lot': 'boardlot'})
    df = df.drop(df[(df.stockcode > 4000) & (df.stockcode < 6030)].index)
    df = df.drop(df[(df.stockcode > 6700) & (df.stockcode < 6800)].index)
    df = df.drop(df[df.stockcode > 10000].index)

    getupdated = pd.read_excel(
        'https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=cols)
    getupdated = getupdated.iloc[0, 0]
    getupdated = getupdated.split()
    lastupdated = {"lastupdated": getupdated[3]}
    update = col_stock_info.insert_one(lastupdated)
    print(update)

    df = df.to_dict('index')
    df = list(df.values())
    insertdf = col_stock_info.insert_many(df)
    print(insertdf.inserted_ids)


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