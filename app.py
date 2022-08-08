import json
import os
import subprocess
from math import ceil
from flask import Flask, redirect, render_template, request, send_from_directory, url_for

import api
from db_pkg.cache import clear_all_cache
from db_pkg.industries import *
from db_pkg.rules import *
from db_pkg.scrape import *
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

		'mkt_overview_data': [{k: v for k, v in d.items() if k != 'last_close_pct'} for d in mkt_overview_data],
		'mkt_overview_last_close_pct': [i["last_close_pct"] for i in mkt_overview_data],
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
	news = scmp_scraping(12)

	forex_data = hkd_exchange_rate_scraping()

	return render_template("home.html",
		chart_data=chart_data,
		card_data=card_data,
		table_data=table_data,
		marquee_data=marquee_data,
		forex_data=forex_data,
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
	hit_cdl_buy_rules, miss_cdl_buy_rules, hit_cdl_sell_rules, miss_cdl_sell_rules = get_rules_results(ticker, True).values()

	return render_template("rules.html", dark_mode=dark_mode, rules={
		"hit_buy_rules": hit_buy_rules,
		"hit_sell_rules": hit_sell_rules,
		"miss_buy_rules": miss_buy_rules,
		"miss_sell_rules": miss_sell_rules,
		"hit_cdl_buy_rules": hit_cdl_buy_rules,
		"hit_cdl_sell_rules": hit_cdl_sell_rules,
		"miss_cdl_buy_rules": miss_cdl_buy_rules,
		"miss_cdl_sell_rules": miss_cdl_sell_rules
	}, stock_info=get_stock_info(ticker), stock_data=get_stock_data_chartjs(ticker, 180), si_data=get_ticker_si_chartjs(ticker))


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
	if request.method == "POST":
		new_buy = json.loads(request.values.get("buy"))
		new_sell = json.loads(request.values.get("sell"))
		print(new_buy, new_sell)
		update_rules("test", new_buy, new_sell, cdl=True)
	return render_template("cdl-rules-edit.html", dark_mode=dark_mode, cdl_buy=rules["cdl_buy"], cdl_sell=rules["cdl_sell"], cdl_patterns=CDL_PATTERNS)


@app.route("/rules/save", methods=["GET", "POST"])
def rules_save():
	save_rules_results(limit=10000, progress=False)
	save_historical_si(limit=10000, progress=False)
	return '', 200


@app.route("/watchlist", methods=["GET"])
def watchlist():
	dark_mode = get_user_theme("test")
	watchlist_data = get_watchlist_data('test')
	table = watchlist_data['table']
	return render_template("watchlist.html", dark_mode=dark_mode, watchlist_data=table, last_updated=watchlist_data['last_updated'].strftime("%d/%m/%Y"), error_msg=None, ticker="")


@app.route("/watchlist", methods=["POST"])
def watchlist_add_ticker():
	ticker = request.values.get("ticker")

	if request.values.get("command") == "add":
		ticker = f"{ticker.rjust(4, '0')}-HK" if len(ticker) < 4 else ticker.replace(".", "-").upper()

		dark_mode = get_user_theme("test")
		watchlist_data = get_watchlist_data('test')
		table = watchlist_data['table']
		error_msg = None
		watchlist_tickers = get_watchlist_tickers('test')

		if ticker in watchlist_tickers:
			error_msg = "Ticker in watchlist already!"
			return render_template("watchlist.html", dark_mode=dark_mode, watchlist_data=table, last_updated=watchlist_data['last_updated'].strftime("%d/%m/%Y"), error_msg=error_msg, ticker=ticker)
		elif not ticker_exists(ticker):
			error_msg = "Ticker not found"
			return render_template("watchlist.html", dark_mode=dark_mode, watchlist_data=table, last_updated=watchlist_data['last_updated'].strftime("%d/%m/%Y"), error_msg=error_msg, ticker=ticker)
		
		add_watchlist('test', ticker)
	elif request.values.get("command") == "delete":
		delete_watchlist('test', ticker)
	
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
	table_data = get_industries_gainers_losers_table()
	industries = get_all_industries()

	if request.method == "POST":
		if industry_exists(request.values.get("industry_detail")):
			industry = request.values.get("industry_detail")
			industry_detail = {industry: get_industry_tickers_info(industry)}
		else:
			industry_detail = {}
		chart_data = None
	else:
		industry_detail = {"Banks": get_industry_tickers_info("Banks")}
		chart_data = {
			"industry_close_pct": get_industry_accum_avg_close_pct_chartjs("Banks", period=60),
			"industry_tickers": get_industry_tickers_accum_close_pct_chartjs("Banks", period=60)
		}

	return render_template("industries.html", dark_mode=dark_mode, table_data=table_data, chart_data=chart_data, industries=industries, industry_detail=industry_detail, indexes=get_ticker_list(ticker_type='index'),)


# @app.route("/industry/<industry>", methods=["GET", "POST"])
# def industry_page(industry):
# 	dark_mode = get_user_theme("test")
# 	if not industry_exists(industry):
# 		return render_template("404.html", dark_mode=dark_mode), 404
# 	return render_template("industry.html", industry=industry, dark_mode=dark_mode)


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
	ticker = request.values.get("ticker", type=str, default="0005-HK")
	ticker = f"{ticker.rjust(4, '0')}-HK" if len(ticker) < 4 else ticker.replace(".", "-").upper()
	if not ticker_exists(ticker):
		return render_template("404.html", dark_mode=dark_mode), 404

	stock_data = get_stock_data_chartjs(ticker=ticker, period=180)
	stock_info = get_stock_info(ticker)

	last_stock_data = get_last_stock_data(ticker)
	stats = {k: last_stock_data[k] for k in [
		"close", "volume", "sma10", "sma20", "sma50", "sma100", "sma250",
		"rsi", "macd", "macd_ema", "macd_div",
		"bbands_upper", "bbands_middle", "bbands_lower",
		"stoch_slowk", "stoch_slowd", "stoch_fastk", "stoch_fastd"
	]}

	news = ticker_news_scraping(ticker)
	
	return render_template("stock-info.html", stock_data=stock_data, stock_info=stock_info, stats=stats, news=news, dark_mode=dark_mode)

# update stock info
@app.route("/stock-info/update", methods=["GET"])
def update_stock_info():
	subprocess.call("python build_db.py", shell=False)
	return '', 200


# stock-analytics
@app.route("/stock-analytics", methods=["GET", "POST"])
def stock_analytics():
	dark_mode = get_user_theme("test")
	ticker = request.values.get("ticker", type=str, default="0005-HK")
	ticker = f"{ticker.rjust(4, '0')}-HK" if len(ticker) < 4 else ticker.replace(".", "-").upper()
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


@app.route("/clear_cache")
def clear_cache():
	clear_all_cache()
	return redirect(url_for("home"))

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
	def camel_to_words(name):
		next_isupper = True
		out = ""
		for char in name:
			if char == "_":
				out += " "
				next_isupper = True
				continue

			if next_isupper:
				out += char.upper()
				next_isupper = False
			else:
				out += char
		return out

	# special cases
	map = {
		"mkt_cap": "Market Cap"
	}

	if name.startswith("stoch"):
		stoch_type = name[6:]
		stoch_type = stoch_type[0].upper() + stoch_type[1:-1]
		return f"{stoch_type} STC %{name[-1].upper()}"
	elif name.startswith("bbands"):
		bbands_type = name[7:]
		bbands_type = bbands_type[0] + bbands_type[1:]
		return f"Bollinger ({bbands_type})"
	elif name.startswith("sma"):
		return f"SMA({name[3:]})"
	elif name.startswith("macd") or name in ["obv", "rsi"]:
		return name.upper().replace('_', ' ')
	elif name in map:
		return map[name]
	else:
		return camel_to_words(name)
	

@app.template_filter('suffix')
def add_suffix(num):
	prefix = "" if num >= 0 else "-"
	num = abs(num)
	if num < 10**3:
		return prefix + "%.2f" % (num)
	elif num < 10**6:
		return prefix + "%.2f" % (num / 10**3) + 'K'
	elif num < 10**9:
		return prefix + "%.2f" % (num / 10**6) + 'M'
	else:
		return prefix + "%.2f" % (num / 10**9) + 'B'

@app.template_filter('format_json')
def format_json(data):
	return json.dumps(data, indent=2, ensure_ascii=False)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
	app.run(port="5000", debug=True)
