from flask import Flask, render_template
from db import *

app = Flask(__name__)

@app.route("/")
def home():
  return render_template("home.html")

@app.route("/", methods=["POST"])
def get_data():
  return render_template("home.html")

if __name__ == "__main__":
  app.run(port="5000", debug=True)