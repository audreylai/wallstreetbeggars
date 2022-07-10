import json
import os
import re
from math import ceil

from flask import Flask, render_template, request, send_from_directory

import api
from db_pkg.industries import *
from db_pkg.news import *
from db_pkg.rules import *
from db_pkg.stock import *
from db_pkg.user import *
from db_pkg.utils import *

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
	period = 60
	all_industry_cmp, all_industry_last_cmp = get_all_industries_close_pct(period=period)
	mkt_overview_data, mkt_overview_last_close_pct = get_mkt_overview_data()
	dark_mode = get_user_theme("test")

	chart_data = {
		'hscc': process_stock_data(get_stock_data('^HSCC', period=period), ticker='^HSCC', period=period),
		'hsce': process_stock_data(get_stock_data('^HSCE', period=period), ticker='^HSCE', period=period),
		'hsi': process_stock_data(get_stock_data('^HSI', period=period), ticker='^HSI', period=period),
		'mkt_overview_data': mkt_overview_data,
		'mkt_overview_last_close_pct': mkt_overview_last_close_pct,
		'all_industry_cmp': all_industry_cmp,
		'all_industry_last_cmp': all_industry_last_cmp
	}

	card_data = {
		'mkt_momentum': chart_data["hsi"]["last_close"] / (chart_data["hsi"]["close"][len(chart_data["hsi"]["close"])-10]['y']),
		'leading_index': sorted({x: chart_data[x]["last_close_pct"] for x in chart_data if x in ["hscc", "hsce", "hsi"]}.items(), key=lambda k: k)[0],
		'leading_industry': all_industry_last_cmp['labels'][-1],
		'leading_industry_pct': all_industry_last_cmp['data'][-1] / 100
	}
	table_data = process_gainers_losers(*get_gainers_losers())
	marquee_data = get_hsi_tickers_data()
	watchlist_rules_data = get_watchlist_rules_results('test')
	news = scmp_scraping(limit=5)

	return render_template("home.html", chart_data=chart_data, card_data=card_data, table_data=table_data, marquee_data=marquee_data, watchlist_rules_data=watchlist_rules_data, news=news, dark_mode=dark_mode)


@app.route("/theme/<theme>", methods=["GET"])
def change_theme(theme):
	update_user_theme("test", theme)
	return ""


@app.route("/rules", methods=["GET", "POST"])
def rules():
	dark_mode = get_user_theme("test")
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")
	if not ticker_exists(ticker):
		return render_template("404.html", dark_mode=dark_mode), 404

	hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = get_rules_results(ticker).values()

	stock_info = get_stock_info(ticker)
	stock_data = process_stock_data(get_stock_data(ticker, period=180), ticker=ticker, period=180)

	return render_template("rules.html", stock_info=stock_info, stock_data=stock_data, dark_mode=dark_mode, rules={
		"hit_buy_rules": hit_buy_rules,
		"hit_sell_rules": hit_sell_rules,
		"miss_buy_rules": miss_buy_rules,
		"miss_sell_rules": miss_sell_rules
	})


@app.route("/rules/edit", methods=["GET", "POST"])
def rules_edit():
	dark_mode = get_user_theme("test")
	rules = get_rules("test")
	if request.method == "POST":
		new_buy = json.loads(request.values.get('buy'))
		new_sell = json.loads(request.values.get('sell'))
		update_rules("test", new_buy, new_sell)
	return render_template("rules-edit.html", dark_mode=dark_mode, buy=rules["buy"], sell=rules["sell"])


@app.route("/rules/save", methods=["GET", "POST"])
def rules_save():
	save_rules_results(limit=500)
	return '', 200

@app.route("/watchlist", methods=["GET", "POST"])
def watchlist():
	return render_template("watchlist.html")

@app.route("/stock-list", methods=["GET", "POST"])
def stock_list_page():
	dark_mode = get_user_theme("test")
	page = request.values.get("page", type=int, default=1)
	filter_industry = request.values.get("filter_industry", type=str, default='')

	min_mkt_cap_pow = request.values.get("min_mkt_cap", type=int, default=9)
	min_mkt_cap = 10 ** min_mkt_cap_pow

	sort_col = request.values.get("sort_col", type=str, default='ticker')
	sort_dir_str = request.values.get("sort_dir", type=str, default='asc')
	sort_dir = pymongo.DESCENDING if sort_dir_str == 'desc' else pymongo.ASCENDING

	stock_table = get_stock_info("ALL", filter_industry, sort_col, sort_dir, min_mkt_cap)

	rows_per_page = 20
	num_of_pages = ceil(len(stock_table["table"]) / rows_per_page)

	page = max(1, min(page, num_of_pages))

	start_index = rows_per_page*(page-1)
	end_index = min(rows_per_page*page+1, len(stock_table["table"]))

	stock_table["table"] = stock_table["table"][start_index:end_index]

	active_tickers = get_active_tickers("test")
	last_updated = stock_table['last_updated'].strftime("%d/%m/%Y")

	return render_template("stock-list.html", stock_table=stock_table['table'], last_updated=last_updated, industries=stock_table['industries'], active_tickers=active_tickers, num_of_pages=num_of_pages, page=page, filter_industry=filter_industry, sort_col=sort_col, sort_dir=sort_dir, min_mkt_cap=min_mkt_cap_pow, dark_mode=dark_mode)

@app.route("/industries", methods=["GET", "POST"])
def industries():
	dark_mode = get_user_theme("test")
	industries_pct = get_all_industries_close_pct(period=60, limit=None)[1]
	gainers, losers = [], []
	for i in range(len(industries_pct['labels'])):
		if industries_pct['data'][i] > 0:
			gainers.append((industries_pct['labels'][i], industries_pct['data'][i]))
		else:
			losers.append((industries_pct['labels'][i], industries_pct['data'][i]))
	table_data, industry_details = process_gainers_losers_industry(gainers[::-1], losers)
	industries = get_all_industries()

	industry_detail = {"Banks": industry_details["Banks"]}
	if request.method == "POST" and request.values.get("industry_detail") in industry_details:
		industry_detail = {request.values.get("industry_detail"): industry_details[request.values.get("industry_detail")]}
	if request.method == "POST" and request.values.get("industry_detail") not in industry_detail:
		industry_detail = {}

	return render_template("industries.html", dark_mode=dark_mode, table_data=table_data, industry_details=industry_details, industries=industries, industry_detail=industry_detail)


# this should be an api
@app.route("/update-active", methods=["POST"])
def update_active():
	if request.form.get("check") == "true":
		update_active_tickers("test", request.form.getlist("tickers[]"))
	else:
		delete_active_tickers("test", request.form.getlist("tickers[]"))
	return {"tickers": request.form.getlist("tickers[]")}


# stock-info
@app.route("/stock-info", methods=["POST", "GET"])
def stock_info():
	dark_mode = get_user_theme("test")
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")

	stock_data = process_stock_data(get_stock_data(ticker, 180), interval=1, ticker=ticker, period=180)
	stock_info = get_stock_info(ticker)
	statistics = {key: get_last_stock_data(ticker)[key] for key in ["close", "volume", "sma10", "sma20", "sma50", "rsi"]} | {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower(): stock_info[key] for key in ["previous_close", "market_cap", "bid", "ask", "beta", "trailing_pe", "trailing_eps", "dividend_rate", "ex_dividend_date"] if key in stock_info}

	news = ticker_news_scraping(ticker)
	
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, statistics=statistics, news=news, dark_mode=dark_mode)

# @app.route("/stock-info/update", methods=["GET"])
# def update_stock_info():
# 	add_stock_info_batch()

# stock-analytics
@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	dark_mode = get_user_theme("test")
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")
	start_datetime, end_datetime = get_datetime_from_period(180)

	if not ticker_exists(ticker):
		return render_template("404.html", dark_mode=dark_mode)

	hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = get_rules_results(ticker).values()

	stock_data = process_stock_data(get_stock_data(ticker, period=180), ticker=ticker, period=180)
	stock_data['start_date'], stock_data['end_date'] = int(start_datetime.timestamp()), int(end_datetime.timestamp())
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info, industries=get_all_industries(), indexes=get_all_tickers(ticker_type='index'), dark_mode=dark_mode,
		rules={
			"hit_buy_rules": hit_buy_rules,
			"hit_sell_rules": hit_sell_rules,
			"miss_buy_rules": miss_buy_rules,
			"miss_sell_rules": miss_sell_rules,
			"buy_pct": len(hit_buy_rules) / (len(hit_buy_rules) + len(miss_buy_rules)),
			"sell_pct": len(hit_sell_rules) / (len(hit_sell_rules) + len(miss_sell_rules))
		}
	)

@app.errorhandler(404)
def page_not_found(e):
	dark_mode = get_user_theme("test")
	return render_template('404.html', dark_mode=dark_mode)

# apis
app.register_blueprint(api.bp)

# template filters
@app.template_filter('epoch_convert')
def timectime(s):
	return datetime.fromtimestamp(s).strftime('%d/%m/%y')

@app.template_filter('get_theme')
def get_theme(username):
	return get_user_theme(username)

@app.template_filter('convert_colname')
def convert_colname(name):
	if name == 'ticker':
		return 'Ticker'
	elif name == 'name':
		return 'Name'
	elif name == 'board_lot':
		return 'Board Lot'
	elif name == 'industry_x':
		return 'Industry'
	elif name == 'mkt_cap':
		return 'Market Cap'
	else:
		return name

@app.template_filter('suffix')
def add_suffix(num):
	if num < 10**3:
		return "%.2f" % (num)
	elif num < 10**6:
		return "%.2f" % (num / 10**3) + 'K'
	elif num < 10**9:
		return "%.2f" % (num / 10**6) + 'M'
	else:
		return "%.2f" % (num / 10**9) + 'B'

@app.template_filter('format_json')
def format_json(data):
	return json.dumps(data, indent=2, ensure_ascii=False)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
	app.run(port="5000", debug=True)
