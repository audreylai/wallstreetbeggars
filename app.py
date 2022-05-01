from flask import Flask, render_template
from db import *

app = Flask(__name__)

@app.route("/")
def hello_world():
  return render_template("base.html")

if __name__ == "__main__":
  app.run(port="5000", debug=True)