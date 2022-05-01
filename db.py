from datetime import *
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