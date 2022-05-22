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


def add_stock_data_one(ticker):
    if not ticker:
        return None

    # Get Ticker Data
    df = yf.download(ticker, period="2y")
    if not df.empty:
        # Dem Tech Indicators
        df["sma10"] = ta.SMA(df["Close"], timeperiod=10)
        df["sma20"] = ta.SMA(df["Close"], timeperiod=20)
        df["sma50"] = ta.SMA(df["Close"], timeperiod=50)
        df["sma100"] = ta.SMA(df["Close"], timeperiod=100)
        df["rsi"] = ta.RSI(df["Close"], timeperiod=14)
        df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df["Close"], fastperiod=12, slowperiod=26, signalperiod=9)

        # Change "date" from index column to regular column
        df = df.reset_index()
        pd.to_datetime(df["Date"])

        # Change keys to all lowercase
        df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
    
    # Convert DataFrame to Dictionary for upsert
    ticker_dict = df.to_dict("records")

    # The actual upsert
    query = { ticker.replace(".","-"): {"$exists": True} }
    col_stock_data.delete_one(query)
    col_stock_data.insert_one({ ticker.replace(".","-"): ticker_dict })


def add_stock_data_batch():
    col_stock_data.drop({})
    for a in range(1,11):
        ticker = "%04d.HK" % a
        df = yf.download(ticker, period="2y")
        if not df.empty:
            # Dem Tech Indicators
            df["sma10"] = ta.SMA(df["Close"], timeperiod=10)
            df["sma20"] = ta.SMA(df["Close"], timeperiod=20)
            df["sma50"] = ta.SMA(df["Close"], timeperiod=50)
            df["rsi"] = ta.RSI(df["Close"], timeperiod=14)
            df["macd"], df["macd_ema"], df["macd_div"] = ta.MACD(df["Close"], fastperiod=12, slowperiod=26, signalperiod=9)
        
            
            # df["macd"] = ta.MACD(df["Close"],fastperiod=12, slowperiod=26, signalperiod=9)
            # print(ta.MACD(df["Close"],fastperiod=12, slowperiod=26, signalperiod=9).mean())
            df = df.reset_index()
            pd.to_datetime(df["Date"])
            df = df.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
            # print(type(df["date"][0]))
        ticker_dict = df.to_dict("records")

        query = { ticker.replace(".","-"): {"$exists": True} }
        # print(query)
        col_stock_data.delete_one(query)
        col_stock_data.insert_one({ ticker.replace(".","-"): ticker_dict })


# Web Scraping Code (etnet)
def etnet_scraping():
    page = requests.get("https://www.etnet.com.hk/www/eng/stocks/industry_adu.php")
    soup = BeautifulSoup(page.content, "html.parser")
    # Fetch the table row with the link
    rows = list(soup.find_all("tr", attrs={"valign": "top"}))
    url_dict = {}
    for x in rows:
        # Fetch the <a> with the link + industry name
        tag = x.find("a")
        url = "https://www.etnet.com.hk/www/eng/stocks/" + tag["href"] # Gets value of attribute :D:D:D:DD::DD::D
        industry = tag.get_text()
        # print(url, industry)
        # Append pair to dictionary
        url_dict[industry] = url
    # print(url_dict)

    scrape_list = []
    for industry in url_dict:
        detailPage = requests.get(url_dict[industry])
        turtleSoup = BeautifulSoup(detailPage.content, "html.parser")
        even_tags = list(turtleSoup.find_all("tr", attrs={"class": "evenRow"}))
        for tag in even_tags:
            # Get Ticker Number
            ticker = tag.find("a").get_text()[-4:] + ".HK"
            nominal = list(tag.find_all("td", attrs={"align": "right"}))[1].get_text()
            turnover = list(tag.find_all("td", attrs={"align": "right"}))[3].get_text()
            mktCap = list(tag.find_all("td", attrs={"align": "right"}))[4].get_text()
            percentYield = list(tag.find_all("td", attrs={"align": "right"}))[5].get_text()
            pe = list(tag.find_all("td", attrs={"align": "right"}))[6].get_text()
            if pe == "":
                pe = "N/A"
            scrape_list.append([ticker,industry,nominal,turnover,mktCap,percentYield,pe])
            
        odd_tags = list(turtleSoup.find_all("tr", attrs={"class": "oddRow"}))
        for tag in odd_tags:
            # Get Ticker Number
            ticker = tag.find("a").get_text()[-4:] + ".HK"
            nominal = list(tag.find_all("td", attrs={"align": "right"}))[1].get_text()
            turnover = list(tag.find_all("td", attrs={"align": "right"}))[3].get_text()
            mktCap = list(tag.find_all("td", attrs={"align": "right"}))[4].get_text()
            percentYield = list(tag.find_all("td", attrs={"align": "right"}))[5].get_text()
            pe = list(tag.find_all("td", attrs={"align": "right"}))[6].get_text()
            if pe == "":
                pe = "N/A"
            scrape_list.append([ticker,industry,nominal,turnover,mktCap,percentYield,pe])
    scrape_df = pd.DataFrame(scrape_list, columns=["stock_code", "industry","nominal","turnover","mkt_cap","pc_yield","pe_ratio"])
    scrape_df = scrape_df.sort_values("stock_code").reset_index(drop=True)
    return(scrape_df)

def add_stock_info():
    # Drops records
    delete = col_stock_info.delete_many({})

    cols = [0, 1, 2, 4]
    df = pd.read_excel(
        'https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=cols, skiprows=2)
    df = df.rename(columns={'Stock Code': 'stock_code', 'Name of Securities': 'name', 'Category': 'category', 'Board Lot': 'board_lot'})
    df = df.drop(df[(df.stock_code > 4000) & (df.stock_code < 6030)].index)
    df = df.drop(df[(df.stock_code > 6700) & (df.stock_code < 6800)].index)
    df = df.drop(df[df.stock_code > 10000].index)

    # Change stock code from numbers to actual tickers
    ticker_name_list = []
    for ticker in list(df["stock_code"]):
        ticker_name = "0000" + str(ticker)
        ticker_name_list.append(ticker_name[-4:] + ".HK")
    df["stock_code"] = ticker_name_list

    # Get last update date
    getupdated = pd.read_excel(
        'https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx', usecols=cols)
    getupdated = getupdated.iloc[0, 0]
    getupdated = getupdated.split()
    lastupdated = {"lastupdated": getupdated[3]}
    update = col_stock_info.insert_one(lastupdated)

    # Extra info via Web Scraping
    # scrape_df = etnet_scraping()
    # df = pd.merge(df, scrape_df, on="stock_code", how="left") # Merge DataFrames by comparing tickers
    # df = df.reset_index(drop=True)

    df = df.to_dict('index')
    df = list(df.values())
    insertdf = col_stock_info.insert_many(df)
    print(insertdf.inserted_ids)


def get_stock_data(ticker, period):
    # Change ticker var to match DB key
    ticker = ticker.upper()
    
    # Calculate start date for fetching
    period = int(period)
    startDate = date.today() + relativedelta(days=-period)
    startDateTime = datetime(startDate.year, startDate.month, startDate.day)
    
    # Fetch and return data
    aggInput = "$" + ticker
    out = col_stock_data.aggregate([
        {
            "$project": {
                ticker: {
                    "$filter": {
                        "input": aggInput,
                        "as": "data",
                        "cond": {"$and": [
                            {"$gte": ["$$data.date", startDateTime]}
                        ]}
                    }
                }
            }
        }
    ])
    res_list = [i for i in out if i[ticker] is not None][0][ticker]
    return res_list

def quick_ticker_fetch(tickers, tickerperiod):
    try:
        ticker = yf.download(tickers, period=tickerperiod)
        # rsi and moving average
        ticker['rsi'] = ta.RSI(ticker['Close'], timeperiod=14)
        ticker['sma10'] = ta.SMA(ticker['Close'], timeperiod=10)
        ticker['sma20'] = ta.SMA(ticker['Close'], timeperiod=20)
        ticker['sma50'] = ta.SMA(ticker['Close'], timeperiod=50)
        ticker['sma100'] = ta.SMA(ticker['Close'], timeperiod=100)
        ticker['sma200'] = ta.SMA(ticker['Close'], timeperiod=200)
        ticker["macd"], ticker["macd_ema"], ticker["macd_div"] = ta.MACD(ticker["Close"], fastperiod=12, slowperiod=26, signalperiod=9)
        
        # remove break days
        ticker = ticker[ticker['Volume'] != 0]
        ticker = ticker.reset_index()
        ticker = ticker.rename(columns={"Date": "date", "Open": "open", "Close": "close", "High": "high", "Low": "low", "Adj Close": "adj_close", "Volume": "volume"})
    except:
        ticker = None
    return ticker

def process_cdl(data):
	out = {
		'sma10': [],
		'sma20': [],
		'sma50': [],
		'macd': [],
		'macd_ema': [],
		'macd_div': [],
		'rsi': [],
		'cdl': [],
		'volume': [],
		'vol_color': []
	}
	max_vol = 0
	
	for i in data:
		if i['volume'] > max_vol:
			max_vol = i['volume']

		out['cdl'].append({
			'x': datetime.timestamp(i['date']) * 1000,
			'o': i['open'],
			'h': i['high'],
			'l': i['low'],
			'c': i['close']
		})

		for col in ['sma10', 'sma20', 'sma50', 'rsi', 'macd', 'macd_div', 'macd_ema', 'volume']:
			out[col].append({
				'x': datetime.timestamp(i['date']) * 1000,
				'y': i[col]
			})

		if i['open'] > i['close']:
			out['vol_color'].append('rgba(215,85,65,0.4)')
		else:
			out['vol_color'].append('rgba(80,160,115,0.4)')

	out['max_vol'] = max_vol
	return out
