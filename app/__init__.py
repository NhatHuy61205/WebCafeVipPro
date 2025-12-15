from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "sdaasasadadss"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Root%40123A@localhost/cafedb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)
