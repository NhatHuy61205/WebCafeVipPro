from flask import Flask, render_template
from CafeApp import app
from CafeApp.models import Mon


@app.route("/")
def index():
    ds_mon = Mon.query.all()
    return render_template("index.html", items=ds_mon)


@app.route("/login")
def login():
    return render_template("layout/login.html")



def get_cart():
    return session.get("cart", {})

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

def cart_stats(cart):
    total_qty = 0
    total_amount = 0.0
    for item in cart.values():
        total_qty += item["quantity"]
        total_amount += item["quantity"] * item["price"]
    return total_qty, total_amount

@app.route("/menu", methods = ['get'])
def menu():
    items = Mon.query.filter(Mon.trangThai == "DANG_BAN").all()
    cart = get_cart()
    total_qty, total_amount = cart_stats(cart)
    return render_template("layout/menu.html",
                           items=items,
                           cart=cart,
                           total_qty=total_qty,
                           total_amount=total_amount)

@app.route("/cart/add", methods = ['post'])
def cart_add():
    mon_id = int(request.form.get("mon_id", 0))
    qty = int(request.form.get("quantity", 1))
    if mon_id <= 0 or qty <= 0:
        return redirect(url_for("menu"))

    mon = Mon.query.get(mon_id)
    if not mon:
        return redirect(url_for("menu"))

    cart = get_cart()
    key = str(mon_id)

    if key not in cart:
        cart[key] = {
            "id": mon.id,
            "name": mon.name,
            "price": float(mon.gia),
            "image": mon.image or "",
            "quantity": 0
        }

    cart[key]["quantity"] += qty
    save_cart(cart)

    return redirect(url_for("menu"))

@app.route("/cart/update", methods = ['post'])
def cart_update():
    mon_id = str(int(request.form.get("mon_id", 0)))
    qty = int(request.form.get("quantity", 1))

    cart = get_cart()
    if mon_id in cart:
        if qty <= 0:
            cart.pop(mon_id, None)
        else:
            cart[mon_id]["quantity"] = qty
        save_cart(cart)

    return redirect(url_for("menu"))

@app.route("/cart/remove", methods = ['post'])
def cart_remove():
    mon_id = str(int(request.form.get("mon_id", 0)))
    cart = get_cart()
    cart.pop(mon_id, None)
    save_cart(cart)
    return redirect(url_for("menu"))


@app.route("/pos")
def pos_page():
    # 1. Kiểm tra quyền nhân viên
    if session.get('role') != 'NHAN_VIEN':
        return redirect(url_for('login'))
        
    # 2. Lấy danh sách món ăn từ DB
    ds_mon = Mon.query.all()
    

@app.route("/admin")
def admin_dashboard():
    # Kiểm tra quyền Admin
    if session.get('role') not in ['QUAN_LY_CUA_HANG', 'QUAN_LY_KHO']:
        return redirect(url_for('login'))
        
    return render_template("admin/dashboard.html")

if __name__=="__main__":
    with app.app_context():
        app.run(debug=True)
