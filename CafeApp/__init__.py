from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = "sdaasasadadss"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Root%40123A@localhost/cafedb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True


VIETQR_CLIENT_ID = "12fd8a9e-7343-472b-ae9b-a370ac11d4a8"
VIETQR_API_KEY = "556aae93-e87b-4a41-ab76-6e040379eae2"

# Tài khoản nhận tiền của bạn
BANK_ACQ_ID = "970422"          # mã ngân hàng (acqId)
BANK_ACCOUNT_NO = "1206059999979"  # số tài khoản
BANK_ACCOUNT_NAME = "BUI NHAT HUY"  # tùy chọn (API dùng để hiển thị)


login = LoginManager(app)
login.login_view = "login"

db = SQLAlchemy(app)
