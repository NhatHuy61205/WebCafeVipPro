from flask import Flask, render_template
from CafeApp import app
from CafeApp.models import Mon


@app.route("/")
def index():
    ds_mon = Mon.query.all()
    return render_template("index.html", items=ds_mon)

@app.route("/menu")
def menu():
    ds_mon = Mon.query.all()
    return render_template("layout/menu.html", items=ds_mon)

@app.route("/login")
def login():
    return render_template("layout/login.html")

if __name__=="__main__":
    with app.app_context():
        app.run(debug=True)