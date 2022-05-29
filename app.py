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
	return render_template("stock-list.html")

@app.route("/stock-analytics")
def stock_analytics():
	data = process_stock_data(get_stock_data('0005-HK', 180))
	return render_template("stock-analytics.html", data=data)

@app.route("/api/close", methods=['GET'])
def api_close():
	ticker_name = request.args.get('ticker')
	return process_close(get_stock_data(ticker_name, 180))

if __name__ == "__main__":
	app.run(port="5000", debug=True)