import json
import os
import re
from math import ceil
import numpy as np


from flask import Flask, redirect, render_template, request, send_from_directory, url_for

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

	mkt_overview_data = get_mkt_overview_table()
	dark_mode = get_user_theme("test")

	chart_data = {
		"hsi_chartjs": get_stock_data_chartjs("^HSI", period),
		"hscc_chartjs": get_stock_data_chartjs("^HSCC", period),
		"hsce_chartjs": get_stock_data_chartjs("^HSCE", period),

		'mkt_overview_data': 		[{k: v for k, v in d.items() if k != 'last_close_pct'} for d in mkt_overview_data],
		'mkt_overview_last_close_pct': [x["last_close_pct"] for x in mkt_overview_data],
		'all_industry_cmp': get_all_industries_accum_avg_close_pct_chartjs(period),
		'all_industry_last_cmp': get_all_industries_avg_last_close_pct_chartjs()
	}
	
	card_data = {
		"mkt_momentum": get_mkt_momentum(),
		"mkt_direction": get_mkt_direction(),
		"leading_index": get_leading_index(),
		"leading_industry": get_leading_industry()
	}

	gainers_data, losers_data = get_gainers_losers_table()
	table_data = {
		"gainers": gainers_data,
		"losers": losers_data
	}
	
	marquee_data = get_hsi_tickers_table()
	watchlist_rules_data = get_watchlist_rules_results('test')
	news = scmp_scraping(5)

	return render_template("home.html",
		chart_data=chart_data,
		card_data=card_data,
		table_data=table_data,
		marquee_data=marquee_data,
		watchlist_rules_data=watchlist_rules_data,
		news=news, dark_mode=dark_mode
	)


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
	# print(hit_buy_rules, miss_buy_rules)
	hit_cdl_buy_rules, miss_cdl_buy_rules, hit_cdl_sell_rules, miss_cdl_sell_rules = get_rules_results(ticker, True).values()
	hit_buy_rules  += hit_cdl_buy_rules
	hit_sell_rules += hit_cdl_sell_rules
	miss_buy_rules += miss_cdl_buy_rules
	miss_sell_rules += miss_cdl_sell_rules
	# print(hit_buy_rules, miss_buy_rules)

	stock_info = get_stock_info(ticker)
	stock_data = get_stock_data_chartjs(ticker=ticker, period=180)

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
		update_rules("test", new_buy, new_sell, cdl=False)
	return render_template("rules-edit.html", dark_mode=dark_mode, buy=rules["buy"], sell=rules["sell"])

@app.route("/cdl/edit", methods=["GET", "POST"])
def cdl_edit():
	dark_mode = get_user_theme("test")
	rules = get_rules("test")
	print(rules["cdl_buy"])
	if request.method == "POST":
		new_buy = json.loads(request.values.get('buy'))
		new_sell = json.loads(request.values.get('sell'))
		update_rules("test", new_buy, new_sell, cdl=True)
	return render_template("cdl-rules-edit.html", dark_mode=dark_mode, cdl_buy=rules["cdl_buy"], cdl_sell=rules["cdl_sell"], candle_names=candle_names)


@app.route("/rules/save", methods=["GET", "POST"])
def rules_save():
	save_rules_results(limit=500)
	return '', 200

@app.route("/watchlist", methods=["GET"])
def watchlist():
	dark_mode = get_user_theme("test")
	watchlist_data = get_watchlist_data('test')
	table = watchlist_data['table']
	average = [(key, np.mean([item[key] for item in table]))if key not in ['ticker', 'name'] else '-' for key in table[0]]
	median = [(key, np.median([item[key] for item in table])) if key not in ['ticker', 'name'] else '-' for key in table[0]]
	total = [(key, np.sum([item[key] for item in table])) if key not in ['ticker', 'name'] else '-' for key in table[0]]
	print(average)
	return render_template("watchlist.html", dark_mode=dark_mode, watchlist_data=table, last_updated=watchlist_data['last_updated'].strftime("%d/%m/%Y"), average=average, median=median, total=total)

@app.route("/watchlist", methods=["POST"])
def watchlist_add_ticker():
	if request.values.get("command") == "add":
		add_watchlist('test', request.values.get("ticker").replace('.', '-').upper())
	elif request.values.get("command") == "delete":
		delete_watchlist('test', request.values.get("ticker").replace('.', '-').upper())
	return redirect(url_for('watchlist'))


@app.route("/stock-list", methods=["GET", "POST"])
def stock_list_page():
	dark_mode = get_user_theme("test")
	page = request.values.get("page", type=int, default=1)
	filter_industry = request.values.get("filter_industry", type=str, default='')

	min_mkt_cap_pow = request.values.get("min_mkt_cap", type=int, default=6)
	min_mkt_cap = 10 ** min_mkt_cap_pow

	sort_col = request.values.get("sort_col", type=str, default='ticker')
	sort_dir_str = request.values.get("sort_dir", type=str, default='asc')
	sort_dir = pymongo.DESCENDING if sort_dir_str == 'desc' else pymongo.ASCENDING

	data = get_stock_info_all(filter_industry, sort_col, sort_dir, min_mkt_cap, ["ticker", "name", "mkt_cap", "industry"])
	rows_per_page = 20
	max_page = ceil(len(data) / rows_per_page)
	page = max(1, min(page, max_page))
	start_index = rows_per_page*(page-1)
	end_index = min(rows_per_page*page+1, len(data))
	data = data[start_index:end_index]

	active_tickers = get_active_tickers("test")
	last_updated = get_last_updated().strftime("%m/%d/%Y %H:%M:%S")

	return render_template("stock-list.html", 
		stock_table=data, last_updated=last_updated, industries=get_all_industries(), 
		active_tickers=active_tickers, page=page, max_page=max_page,
		filter_industry=filter_industry, sort_col=sort_col, sort_dir=sort_dir, 
		min_mkt_cap=min_mkt_cap_pow, dark_mode=dark_mode, page_btns=get_pagination_btns(page, max_page)
	)

@app.route("/industries", methods=["GET", "POST"])
def industries_page():
	dark_mode = get_user_theme("test")
	industries_pct = get_all_industries_avg_last_close_pct()
	table_data = get_industries_gainers_losers_table()
	industries = get_all_industries()

	industry_detail = {"Banks": get_industry_tickers_last_close_pct("Banks")}
	if request.method == "POST":
		if industry_exists(request.values.get("industry_detail")):
			industry_detail = {request.values.get("industry_detail"): get_industry_tickers_last_close_pct(request.values.get("industry_detail"))}
		else:
			industry_detail = {}
		print(industry_detail)

	return render_template("industries.html", dark_mode=dark_mode, table_data=table_data, industries=industries, industry_detail=industry_detail)


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

	stock_data = get_stock_data_chartjs(ticker=ticker, period=180)
	stock_info = get_stock_info(ticker)
	statistics = {key: get_last_stock_data(ticker)[key] for key in ["close", "volume", "sma10", "sma20", "sma50", "rsi"]} | {re.sub('([A-Z])', r' \1', key)[:1].upper() + re.sub('([A-Z])', r' \1', key)[1:].lower(): stock_info[key] for key in ["previous_close", "market_cap", "bid", "ask", "beta", "trailing_pe", "trailing_eps", "dividend_rate", "ex_dividend_date"] if key in stock_info}

	news = ticker_news_scraping(ticker)
	
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, statistics=statistics, news=news, dark_mode=dark_mode)

# @app.route("/stock-info/update", methods=["GET"])
# def update_stock_info():
# 	build_db_2.main()

# stock-analytics
@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	dark_mode = get_user_theme("test")
	ticker = request.values.get("ticker", type=str, default='0005-HK').upper().replace(".", "-")

	if not ticker_exists(ticker):
		return render_template("404.html", dark_mode=dark_mode)

	hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = get_rules_results(ticker).values()

	stock_data = get_stock_data_chartjs(ticker=ticker, period=180)
	stock_info = get_stock_info(ticker)

	return render_template("stock-analytics.html", stock_data=stock_data, stock_info=stock_info, industries=get_all_industries(), indexes=get_ticker_list(ticker_type='index'), dark_mode=dark_mode,
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
	elif name == 'industry':
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
