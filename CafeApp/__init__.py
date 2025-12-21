import re

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
import os
from CafeApp.inventory_bot import start_inventory_scheduler



app = Flask(__name__)
app.secret_key = "sdaasasadadss"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Root%40123A@localhost/cafedb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
PAGE_SIZE = 10
MAX_CART_ITEMS = 10
PHONE_RE = re.compile(r"^0\d{9}$")

VIETQR_CLIENT_ID = "12fd8a9e-7343-472b-ae9b-a370ac11d4a8"
VIETQR_API_KEY = "556aae93-e87b-4a41-ab76-6e040379eae2"
VIETQR_TEMPLATE_ID = "akGFPiZ"

# Tài khoản nhận tiền của bạn
BANK_ACQ_ID = "970422"          # mã ngân hàng (acqId)
BANK_ACCOUNT_NO = "1206059999979"  # số tài khoản
BANK_ACCOUNT_NAME = "BUI NHAT HUY"  # tùy chọn (API dùng để hiển thị)


login = LoginManager(app)
login.login_view = "login"


cloudinary.config(
    cloud_name = "duybrbxoz",
    api_key = "862299828767341",
    api_secret = "qesiGf5atKtSUg0_xGXE8x16cjA"
 )
db = SQLAlchemy(app)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    start_inventory_scheduler(app, db)