from flask import Flask, render_template, request
import datetime
from db import *

app = Flask(__name__)

@app.route("/")
def home():
	data = process_stock_data(get_stock_data('0005-HK', 60))
	return render_template("home.html", data=data)

@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")

@app.route("/rules")
def rules():
	return render_template("rules.html")

@app.route("/stock-list")
def stock_list():
	# GIVE ME DATA
	stock_table = get_stock_info("all")
	# last_update = stock_table['last_update'].strftime("%d/%m/%Y")
	last_update = stock_table['last_update']
	return render_template("stock-list.html", stock_table=stock_table['table'], last_update=last_update, industries=stock_table['industries'])

@app.route("/stock-info")
def stock_info():
	# GIVE ME DATA
	return render_template("stock-info.html")

@app.route("/stock-analytics")
def stock_analytics():
	data = process_stock_data(get_stock_data('0005-HK', 180))
	return render_template("stock-analytics.html", data=data)

@app.route("/api/get_stock_close_pct", methods=['GET'])
def api_get_stock_close_pct():
	ticker_name = request.args.get('ticker')
	data = get_stock_data(ticker_name, 180)
	return process_close(data)

@app.route("/api/get_industry_close_pct", methods=['GET'])
def api_get_industry_close_pct():
	industry_name = request.args.get('industry')
	print('AAAAAAAAAA', industry_name)
	data = get_industry_close_pct(industry_name, 180)
	return process_industry_avg(data)

if __name__ == "__main__":
	app.run(port="5000", debug=True)