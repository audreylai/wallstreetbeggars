from flask import Flask, render_template
import datetime
from db import *

app = Flask(__name__)


@app.route("/")
def home():
	data = process_cdl(get_stock_data('0005-HK', 60))
	return render_template("home.html", data=data)

@app.route("/", methods=["POST"])
def get_data():
	return render_template("home.html")

@app.route("/rules")
def rules():
	return render_template("rules.html")

@app.route("/stock-info")
def stock_info():
	data = process_cdl(get_stock_data('0005-HK', 60))
	return render_template("stock-info.html", data=data)

if __name__ == "__main__":
	app.run(port="5000", debug=True)