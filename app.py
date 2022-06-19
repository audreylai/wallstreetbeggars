import re

from math import ceil

from flask import Flask, render_template, request

from db import *
from utils import *
import api

app = Flask(__name__)

@app.route("/")
def home():
	data = process_stock_data(get_stock_data('0005-HK', period=60))
	return render_template("home.html", data=data)


@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")


@app.route("/rules")
def rules():
	return render_template("rules.html")


@app.route("/stock-list", methods=["GET", "POST"])
def stock_list_page():
	page = request.values.get("page", type=int, default=1)
	filter_industry = request.values.get("filter_industry", type=str, default='')
	sort_col = request.values.get("sort_col", type=str, default='ticker')
	sort_dir_str = request.values.get("sort_dir", type=str, default='asc')
	sort_dir = pymongo.DESCENDING if sort_dir_str == 'desc' else pymongo.ASCENDING

	stock_table = get_stock_info("ALL", filter_industry, sort_col, sort_dir)

	rows_per_page = 20
	num_of_pages = ceil(len(stock_table["table"]) / rows_per_page)

	page = max(1, min(page, num_of_pages))

	start_index = rows_per_page*(page-1)
	end_index = min(rows_per_page*page+1, len(stock_table["table"]))

	stock_table["table"] = stock_table["table"][start_index:end_index]

	active_tickers = get_active_tickers("test")['active']
	last_updated = stock_table['last_updated'].strftime("%d/%m/%Y")
	return render_template("stock-list.html", stock_table=stock_table['table'], last_updated=last_updated, industries=stock_table['industries'], active_tickers=active_tickers, num_of_pages=num_of_pages, page=page, filter_industry=filter_industry, sort_col=sort_col, sort_dir=sort_dir)


# this should be an api
@app.route("/update-active", methods=["POST"])
def update_active():
	# todo: write update db logic
	print(request.form.get("check"), request.form.getlist("tickers[]"))
	if request.form.get("check") == "true":
		update_active_tickers("test", request.form.getlist("tickers[]"))
	else:
		delete_active_tickers("test", request.form.getlist("tickers[]"))
	return {"tickers": request.form.getlist("tickers[]")}


# stock-info
@app.route("/stock-info", methods=["POST", "GET"])
def stock_info():
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")

	stock_data = process_stock_data(get_stock_data(ticker, 180), 1)
	stock_data['ticker'] = ticker
	stock_info = get_stock_info(ticker)
	statistics = {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower(): stock_data[key] for key in ["close", "volume", "sma10", "sma20", "sma50", "rsi"]} | {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower() : stock_info[key] for key in ["previousClose", "marketCap", "bid", "ask", "beta", "trailingPE", "trailingEps", "dividendRate", "exDividendDate"] if key in stock_info}
		
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, statistics=statistics)


# stock-analytics
@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")
	start_datetime, end_datetime = get_datetime_from_period(180)

	if not ticker_exists(ticker):
		return 'not found', 404 # proper error page later
	
	stock_data = process_stock_data(get_stock_data(ticker, period=180))
	stock_data['ticker'], stock_data['period'], stock_data['interval'] = ticker, 180, 1
	stock_data['start_date'], stock_data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info, industries=get_all_industries(), indexes=get_all_tickers(ticker_type='index'))

# apis
app.register_blueprint(api.bp)

# template filters
@app.template_filter('epoch_convert')
def timectime(s):
	return datetime.fromtimestamp(s).strftime('%d/%m/%y')

@app.template_filter('suffix')
def add_suffix(num):
    if num < 10**3:
        return "%.1f" % (num)
    elif num < 10**6:
        return "%.1f" % (num / 10**3) + 'K'
    elif num < 10**9:
        return "%.1f" % (num / 10**6) + 'M'
    else:
        return "%.1f" % (num / 10**9) + 'B'


if __name__ == "__main__":
	app.run(port="5000", debug=True)
