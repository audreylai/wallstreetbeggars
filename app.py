from flask import Flask
from db import *

app = Flask(__name__)

@app.route("/")
def hello_world():
  return "<p>Hello, World!</p>"

if __name__ == "__main__":
  app.run(port="5000", debug=True)