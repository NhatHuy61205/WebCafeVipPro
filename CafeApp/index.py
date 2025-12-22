import base64
import datetime
import io
import math
import re
from functools import wraps
import urllib.parse
from typing import Optional
import qrcode
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import  or_
from CafeApp.dao import get_drink_form_defaults, upsert_drink_to_cart, make_drink_option_key, \
    count_unread_thong_bao_kho, get_latest_thong_bao_kho, mark_thong_bao_kho_as_read, delete_thong_bao_kho

from CafeApp import admin_app, VIETQR_TEMPLATE_ID
from CafeApp.models import KhachHang, HoaDon, ChiTietHoaDon, Mon, NhanVienCuaHang, LoaiQREnum, TrangThaiQREnum, \
    ThongBao, ChiTietHoaDonTopping, NhomMonEnum, TrangThaiEnum, TrangThaiThongBaoKhoEnum, ThongBaoKho
from CafeApp.models import LoaiDungEnum, TrangThaiHoaDonEnum, SizeEnum
from CafeApp.models import LoaiMonEnum, QRCode
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, flash, current_app, \
    make_response
from CafeApp import app, db, BANK_ACQ_ID, BANK_ACCOUNT_NO, BANK_ACCOUNT_NAME, dao, login, PAGE_SIZE, MAX_CART_ITEMS, \
    PHONE_RE
from CafeApp.dao import build_drink, normalize_topping_codes, get_drink_static_opts, get_topping_opts_for_mon, \
    upsert_hoa_don_from_pos_cart, pay_from_pos_cart, confirm_table_by_qr
from urllib.parse import quote, unquote


def normalize_items(items):

    out = []
    for it in items or []:
        get = (lambda k, default=None: it.get(k, default)) if isinstance(it, dict) else (lambda k, default=None: getattr(it, k, default))

        ten = get("ten") or get("name") or ""
        sl = get("sl")
        if sl is None:
            sl = get("qty", 0)
        tien = get("tien")
        if tien is None:
            tien = get("line_total", 0)

        desc = get("desc") or []
        out.append({"ten": ten, "sl": sl, "tien": tien, "desc": desc})
    return out

def query_mon_list(q=None, category=None):
    query = Mon.query

    if hasattr(Mon, "trangThai"):
        query = query.filter(Mon.trangThai == "DANG_BAN")

    if q:
        keyword = f"%{q.strip()}%"
        conds = [Mon.name.ilike(keyword)]
        if hasattr(Mon, "moTa"):
            conds.append(Mon.moTa.ilike(keyword))
        query = query.filter(or_(*conds))

    if category and category != "ALL":
        query = query.filter(Mon.nhom == NhomMonEnum[category].value)

    return query

def make_qr_data_uri(text: str) -> str:
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return "data:image/png;base64," + b64

def cart_too_many(cart: dict, max_items: int = MAX_CART_ITEMS) -> bool:
    return len(cart) >= max_items


def check_cart_limit_or_redirect(
        cart: dict,
        option_key: str,
        redirect_endpoint: str = "pos_page",
        redirect_kwargs: Optional[dict] = None,
        message: str = "Quá số lượng món trên hóa đơn (tối đa 10 món khác nhau).",
        edit_key: Optional[str] = None,
):
    if redirect_kwargs is None:
        redirect_kwargs = {}

    effective_len = len(cart) - (1 if (edit_key and edit_key in cart) else 0)

    if option_key not in cart and effective_len >= MAX_CART_ITEMS:
        flash(message, category="warning")
        return redirect(url_for(redirect_endpoint, **redirect_kwargs))

    return None


def block_when_checkout(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("checkout_mode"):
            return redirect(url_for("menu"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    page = request.args.get("page", 1, type=int)

    base_q = Mon.query.filter(Mon.trangThai == "DANG_BAN")

    total_items = base_q.count()
    pages = max(1, math.ceil(total_items / PAGE_SIZE))

    if page < 1:
        page = 1
    if page > pages:
        page = pages

    items = (
        base_q
        .order_by(Mon.id.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    return render_template(
        "index.html",
        items=items,
        page=page,
        pages=pages
    )


@app.route("/login", methods=["GET", "POST"], endpoint="login")
def login_my_user():
    print("== HIT /login ==", request.method)  # <-- thêm
    if request.method == "POST":
        print("FORM =", dict(request.form))  # <-- thêm

    if current_user.is_authenticated:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
        print("ALREADY AUTH, role =", role_str)  # <-- thêm
        if role_str == "NHAN_VIEN":
            return redirect(url_for("pos_page"))
        elif role_str in ["QUAN_LY_CUA_HANG", "QUAN_LY_KHO"]:
            return redirect(url_for("admin_dashboard"))
        return redirect("/")

    err_msg = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_user(username, password)
        print("AUTH USER =", bool(user))  # <-- thêm

        if user:
            try:
                if getattr(user, "trangThai", None) == TrangThaiEnum.INACTIVE:
                    err_msg = "Tài khoản đã bị khóa (INACTIVE), không thể đăng nhập!"
                    return render_template("login.html", err_msg=err_msg)
            except Exception:
                err_msg = "Tài khoản không hợp lệ!"
                return render_template("login.html", err_msg=err_msg)
            login_user(user)
            print("LOGIN_USER DONE. current_user.auth =", current_user.is_authenticated)  # <-- thêm

            role_str = user.role.value if hasattr(user.role, "value") else user.role
            session["role"] = role_str
            print("SET session role =", session.get("role"))  # <-- thêm

            if role_str == "NHAN_VIEN":
                return redirect(url_for("pos_page"))
            elif role_str in ["QUAN_LY_CUA_HANG", "QUAN_LY_KHO"]:
                return redirect(url_for("admin_dashboard"))
            else:
                err_msg = "Tài khoản không có quyền truy cập!"
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/admin-login", methods=["POST"])
def admin_login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = dao.auth_user(username, password)

    if user:
        try:
            if getattr(user, "trangThai", None) == TrangThaiEnum.INACTIVE:
                flash("Tài khoản đã bị khóa (INACTIVE), không thể đăng nhập!", "danger")
                return redirect(url_for("login_my_user"))
        except Exception:
            flash("Tài khoản không hợp lệ!", "danger")
            return redirect(url_for("login_my_user"))
        role_str = user.role.value if hasattr(user.role, "value") else user.role
        if role_str not in ["QUAN_LY_CUA_HANG", "QUAN_LY_KHO"]:
            flash("Bạn không có quyền truy cập Admin!", "danger")
            return redirect(url_for("login_my_user"))

        login_user(user)
        session["role"] = role_str
        return redirect(url_for("admin_dashboard"))

    flash("Tài khoản hoặc mật khẩu không đúng!", "danger")
    return redirect(url_for("login_my_user"))


@app.route("/logout", endpoint="logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))


@app.route("/drink/<int:mon_id>", methods=["GET", "POST"])
def drink_config(mon_id):
    mon = Mon.query.get_or_404(mon_id)

    if mon.loaiMon != LoaiMonEnum.NUOC:
        return redirect(url_for("menu"))

    SIZE_OPTS, SUGAR_OPTS, ICE_OPTS = get_drink_static_opts()
    TOPPING_OPTS = get_topping_opts_for_mon(mon)

    # ====== GET ======
    if request.method == "GET":
        cart = get_cart() or {}
        edit_key = (request.args.get("edit_key") or "").strip()

        form = get_drink_form_defaults(cart, edit_key)
        form["topping"] = normalize_topping_codes(form.get("topping", []), TOPPING_OPTS)

        unit_price, desc_list = build_drink(mon, form["size"], form["duong"], form["da"], form["topping"])
        try:
            qty = int(form.get("quantity") or 1)
        except:
            qty = 1
        total_price = unit_price * max(qty, 1)

        next_url = (request.args.get("next") or url_for("menu"))

        return render_template(
            "drink_modal.html",
            mon=mon,
            form=form,
            errors={},
            unit_price=unit_price,
            total_price=total_price,
            desc_list=desc_list,
            SIZE_OPTS=SIZE_OPTS,
            SUGAR_OPTS=SUGAR_OPTS,
            ICE_OPTS=ICE_OPTS,
            TOPPING_OPTS=TOPPING_OPTS,
            edit_key=edit_key or None,
            next_url=next_url
        )

    # ====== POST ======
    size = (request.form.get("size") or "S").strip()
    duong = (request.form.get("duong") or "70").strip()
    da = (request.form.get("da") or "70").strip()
    topping = request.form.getlist("topping")
    note = (request.form.get("note") or "").strip()
    qty_raw = (request.form.get("quantity") or "1").strip()
    edit_key = (request.form.get("edit_key") or "").strip()
    next_url = (request.form.get("next") or url_for("menu"))
    action = (request.form.get("action") or "").strip()

    topping = normalize_topping_codes(topping, TOPPING_OPTS)

    errors = {}
    try:
        qty = int(qty_raw)
        if qty < 1:
            raise ValueError()
    except:
        errors["quantity"] = "Số lượng không hợp lệ."
        qty = 1

    unit_price, desc_list = build_drink(mon, size, duong, da, topping)
    total_price = unit_price * qty

    # Nếu chưa bấm add hoặc có lỗi -> render lại modal
    if action != "add" or errors:
        form = {
            "size": size,
            "duong": duong,
            "da": da,
            "topping": topping,
            "note": note,
            "quantity": qty_raw
        }
        return render_template(
            "drink_modal.html",
            mon=mon,
            form=form,
            errors=errors,
            unit_price=unit_price,
            total_price=total_price,
            desc_list=desc_list,
            SIZE_OPTS=SIZE_OPTS,
            SUGAR_OPTS=SUGAR_OPTS,
            ICE_OPTS=ICE_OPTS,
            TOPPING_OPTS=TOPPING_OPTS,
            edit_key=edit_key or None,
            next_url=next_url
        )

    # ====== Add/Update cart (dùng service trong dao.py) ======
    cart = get_cart() or {}

    # Tạo key chuẩn để check limit (quan trọng với edit_key)
    option_key = make_drink_option_key(mon.id, size, duong, da, topping, note)

    resp = check_cart_limit_or_redirect(
        cart=cart,
        option_key=option_key,
        redirect_endpoint="menu",
        redirect_kwargs={},
        message="Giỏ hàng chỉ tối đa 10 món khác nhau.",
        edit_key=edit_key
    )
    if resp:
        flash("Giỏ hàng chỉ tối đa 10 món khác nhau.", "warning")
        return redirect(next_url)

    cart, _, _, _, _ = upsert_drink_to_cart(
        cart=cart,
        mon=mon,
        size=size,
        duong=duong,
        da=da,
        toppings=topping,
        note=note,
        qty_raw=qty_raw,
        edit_key=edit_key
    )

    save_cart(cart)
    return redirect(next_url or url_for("menu"))



@app.route("/drink/edit/<path:cart_key>", methods=["GET"])
def drink_edit(cart_key):
    cart = get_cart()
    cart_key = unquote(cart_key)
    next_url = (request.args.get("next") or url_for("menu"))

    if cart_key not in cart:
        return redirect(url_for("menu"))

    item = cart[cart_key]
    mon = Mon.query.get_or_404(item["id"])

    if mon.loaiMon != LoaiMonEnum.NUOC:
        return redirect(url_for("menu"))

    opt = item.get("options", {})
    form = {
        "size": opt.get("size", "S"),
        "duong": opt.get("duong", "70"),
        "da": opt.get("da", "70"),
        "topping": opt.get("topping", []),
        "note": opt.get("note", ""),
        "quantity": str(item.get("quantity", 1))
    }

    SIZE_OPTS, SUGAR_OPTS, ICE_OPTS = get_drink_static_opts()
    TOPPING_OPTS = get_topping_opts_for_mon(mon)

    form["topping"] = normalize_topping_codes(form["topping"], TOPPING_OPTS)

    unit_price, desc_list = build_drink(mon, form["size"], form["duong"], form["da"], form["topping"])
    total_price = unit_price * int(form["quantity"] or 1)

    return render_template(
        "drink_modal.html",
        mon=mon,
        form=form,
        errors={},
        unit_price=unit_price,
        total_price=total_price,
        desc_list=desc_list,
        SIZE_OPTS=SIZE_OPTS,
        SUGAR_OPTS=SUGAR_OPTS,
        ICE_OPTS=ICE_OPTS,
        TOPPING_OPTS=TOPPING_OPTS,
        edit_key=cart_key,
        next_url=next_url
    )


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


# ==== Menu Khách Online

@app.route("/menu", methods=["GET"])
def menu():
    page = request.args.get("page", 1, type=int)
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "ALL").strip()


    if category == "TRA_SUA":
        category = "TRA"

    base_q = Mon.query.filter(Mon.trangThai == "DANG_BAN")

    if q:
        kw = f"%{q}%"
        conds = [Mon.name.ilike(kw)]
        if hasattr(Mon, "moTa"):
            conds.append(Mon.moTa.ilike(kw))
        base_q = base_q.filter(or_(*conds))

    if category != "ALL":
        base_q = base_q.filter(Mon.nhom == category)

    # ===== pagination =====
    total_items = base_q.count()
    pages = max(1, math.ceil(total_items / PAGE_SIZE))

    if page < 1:
        page = 1
    if page > pages:
        page = pages

    items = (base_q
             .order_by(Mon.id.desc())
             .offset((page - 1) * PAGE_SIZE)
             .limit(PAGE_SIZE)
             .all())

    # ===== cart =====
    cart = get_cart()
    if not cart:
        session.pop("checkout_mode", None)
        session.modified = True

    total_qty, total_amount = cart_stats(cart)
    service_fee = total_amount * 0.05
    grand_total = total_amount + service_fee

    checkout_mode = bool(session.get("checkout_mode", False))

    return render_template(
        "menu.html",
        items=items,
        page=page,
        pages=pages,
        q=q,
        category=category,

        cart=cart,
        total_qty=total_qty,
        total_amount=total_amount,
        LoaiMonEnum=LoaiMonEnum,
        show_checkout=checkout_mode,
        checkout_mode=checkout_mode,
        errors=session.pop("checkout_errors", {}),
        checkout_form=session.pop("checkout_form", {"name": "", "phone": "", "address": ""}),
        service_fee=service_fee,
        grand_total=grand_total
    )


# ==== Giỏ hàng của khách Online

@app.route("/cart/add", methods=["POST"])
@block_when_checkout
def cart_add():
    mon_id = int(request.form.get("mon_id", 0))
    qty_raw = (request.form.get("quantity", "1") or "1").strip()

    try:
        qty = int(qty_raw)
    except:
        qty = 1

    if mon_id <= 0 or qty <= 0:
        return redirect(url_for("menu"))

    mon = Mon.query.get(mon_id)
    if not mon:
        return redirect(url_for("menu"))

    cart = get_cart() or {}
    key = str(mon_id)

    resp = check_cart_limit_or_redirect(
        cart=cart,
        option_key=key,
        redirect_endpoint="menu",
        redirect_kwargs={},  # nếu cần giữ page: {"page": page}
        message="Giỏ hàng chỉ tối đa 10 món khác nhau.",
        edit_key=None
    )
    if resp:
        return resp

    if key not in cart:
        cart[key] = {
            "id": mon.id,
            "name": mon.name,
            "price": float(mon.gia),
            "image": mon.image or "",
            "quantity": 0,
            "options": None
        }

    cart[key]["quantity"] += qty
    save_cart(cart)
    return redirect(request.referrer or url_for("menu"))


@app.route("/cart/inc", methods=['POST'])
@block_when_checkout
def cart_inc():
    key = (request.form.get("key") or request.form.get("mon_id") or "").strip()
    cart = get_cart()

    if key in cart:
        cart[key]["quantity"] += 1
        save_cart(cart)

    return redirect(request.referrer or url_for("menu"))


@app.route("/cart/dec", methods=['POST'])
@block_when_checkout
def cart_dec():
    key = (request.form.get("key") or request.form.get("mon_id") or "").strip()
    cart = get_cart()

    if key in cart:
        cart[key]["quantity"] -= 1
        if cart[key]["quantity"] <= 0:
            cart.pop(key, None)
        save_cart(cart)

    return redirect(request.referrer or url_for("menu"))


@app.route("/cart/update", methods=['POST'])
@block_when_checkout
def cart_update():
    key = (request.form.get("key") or request.form.get("mon_id") or "").strip()
    qty_raw = (request.form.get("quantity") or "1").strip()

    cart = get_cart()
    if key in cart:
        try:
            qty = int(qty_raw)
        except:
            qty = cart[key]["quantity"]  # nhập bậy thì giữ nguyên

        if qty <= 0:
            cart.pop(key, None)
        else:
            cart[key]["quantity"] = qty

        save_cart(cart)

    return redirect(request.referrer or url_for("menu"))


@app.route("/cart/remove", methods=['POST'])
@block_when_checkout
def cart_remove():
    key = (request.form.get("key") or request.form.get("mon_id") or "").strip()
    cart = get_cart()
    cart.pop(key, None)
    save_cart(cart)
    return redirect(request.referrer or url_for("menu"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    session.pop("cart", None)
    session.pop("checkout_mode", None)
    session.modified = True
    return redirect(request.referrer or url_for("menu"))


# Thanh Toán - Khách Hàng Online

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()
    if not cart:
        # giỏ rỗng thì chắc chắn tắt checkout mode
        session.pop("checkout_mode", None)
        session.modified = True
        return redirect(url_for("menu"))

    total_qty, total_amount = cart_stats(cart)
    service_fee = total_amount * 0.05
    grand_total = total_amount + service_fee

    # bật chế độ checkout để UI lock cart
    session["checkout_mode"] = True
    session.modified = True

    errors = {}
    form = {"name": "", "phone": "", "address": ""}

    if request.method == "POST":
        # ===== 1) validate =====
        form["name"] = (request.form.get("name") or "").strip()
        form["phone"] = (request.form.get("phone") or "").strip()
        form["address"] = (request.form.get("address") or "").strip()

        if not form["name"]:
            errors["name"] = "Vui lòng nhập tên."
        if not form["phone"]:
            errors["phone"] = "Vui lòng nhập số điện thoại."
        elif (not form["phone"].isdigit()) or len(form["phone"]) != 10:
            errors["phone"] = "Số điện thoại phải đủ 10 số."
        if not form["address"]:
            errors["address"] = "Vui lòng nhập địa chỉ."

        if not errors:
            # ===== 2) upsert khách hàng theo sdt =====
            kh = KhachHang.query.filter_by(sdt=form["phone"]).first()
            if not kh:
                kh = KhachHang(
                    name=form["name"],
                    sdt=form["phone"],
                    diaChi=form["address"],
                    loaiKhachHang=LoaiDungEnum.TAI_NHA
                )
                db.session.add(kh)
                db.session.flush()  # lấy kh.id (chưa commit)
            else:
                kh.name = form["name"]
                kh.diaChi = form["address"]
                if not kh.loaiKhachHang:
                    kh.loaiKhachHang = LoaiDungEnum.TAI_NHA

            # ===== 3) tạo hóa đơn CHỜ THANH TOÁN =====
            hd = HoaDon(
                name="HD",
                ngayThanhToan=None,
                soBan=None,
                tongTienHang=float(total_amount),
                thue=0.0,
                phiPhucVu=float(service_fee),
                giamGia=0.0,
                tongThanhToan=float(grand_total),
                loaiHoaDon=LoaiDungEnum.TAI_NHA,
                trangThai=TrangThaiHoaDonEnum.CHO_THANH_TOAN,
                khachHang_id=kh.id
            )
            db.session.add(hd)
            db.session.flush()  # lấy hd.id để gắn chi tiết

            # ===== 4) tạo chi tiết hóa đơn từ cart =====
            for item in cart.values():
                qty = int(item.get("quantity", 0))
                price = float(item.get("price", 0.0))
                if qty <= 0:
                    continue

                opts = item.get("options") or {}
                size = opts.get("size") or SizeEnum.S
                muc_duong = int(opts.get("mucDuong", 100))
                muc_da = int(opts.get("mucDa", 100))

                ct = ChiTietHoaDon(
                    soLuong=qty,
                    donGia=price,
                    thanhTien=price * qty,
                    ghiChu=None,
                    size=size,
                    mucDuong=muc_duong,
                    mucDa=muc_da,
                    hoaDon_id=hd.id,
                    mon_id=int(item["id"])
                )
                db.session.add(ct)

            db.session.flush()

            # ===== 5) set mã tham chiếu cho chuyển khoản =====
            # (đảm bảo bạn đã thêm cột maThamChieu vào HoaDon)
            hd.name = f"HD{hd.id:06d}"
            hd.maThamChieu = f"HD{hd.id}"

            # commit tất cả
            db.session.commit()

            # ===== 6) clear cart + tắt checkout mode =====
            session.pop("cart", None)
            session.pop("checkout_mode", None)
            session.modified = True

            # ===== 7) chuyển sang trang QR =====
            return redirect(url_for("payment_qr", hoa_don_id=hd.id))

    # ===== GET hoặc POST có lỗi: render lại menu ở chế độ checkout =====
    items = Mon.query.filter(Mon.trangThai == "DANG_BAN").all()
    return render_template(
        "menu.html",
        items=items,
        cart=cart,
        total_qty=total_qty,
        total_amount=total_amount,
        LoaiMonEnum=LoaiMonEnum,
        show_checkout=True,
        checkout_mode=True,
        errors=errors,
        checkout_form=form,
        service_fee=service_fee,
        grand_total=grand_total
    )


@app.route("/checkout/start", methods=["POST"])
def checkout_start():
    session["checkout_mode"] = True
    session.modified = True
    return redirect(url_for("menu"))


@app.route("/checkout/cancel", methods=["POST"])
def checkout_cancel():
    session.pop("checkout_mode", None)
    session.modified = True
    return redirect(url_for("menu"))


@app.route("/checkout/done", methods=["GET"])
def checkout_done():
    # trang trắng placeholder – lát bạn yêu cầu làm tiếp
    return render_template("checkout_done.html")


# ===== Thanh Toán QR Code Tự Động - Webhook

@app.route("/webhook/sepay", methods=["POST"])
def sepay_webhook():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"ok": True, "message": "no data"}), 200

    amount = data.get("transferAmount", None)
    if amount is None:
        amount = data.get("amount", 0)
    try:
        amount = int(float(amount))
    except:
        amount = 0

    content = (data.get("content") or "").strip()
    description = (data.get("description") or "").strip()

    status = (data.get("status") or "").strip().upper()
    transfer_type = (data.get("transferType") or data.get("type") or "").strip().lower()

    # chỉ xử lý tiền vào
    if transfer_type and transfer_type != "in":
        return jsonify({"ok": True, "message": "ignore (not incoming)"}), 200

    text = f"{description} {content}".strip()

    # bắt mã HD dễ hơn (HD15, HD000123...)
    m = re.search(r"HD\d+", text)
    if not m:
        return jsonify({"ok": True, "message": "ignore (no HD code)"}), 200

    ma_hd = m.group(0)

    # nếu có status thì chỉ nhận SUCCESS
    if status and status != "SUCCESS":
        return jsonify({"ok": True, "message": f"ignore (status={status})"}), 200

    hoa_don = HoaDon.query.filter_by(maThamChieu=ma_hd).first()
    if not hoa_don:
        return jsonify({"ok": True, "message": f"ignore (HoaDon {ma_hd} not found)"}), 200

    if hoa_don.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN:
        return jsonify({"ok": True, "message": "already paid"}), 200

    try:
        expected = int(round(float(hoa_don.tongThanhToan)))
    except:
        expected = 0

    if expected != amount:
        return jsonify({
            "ok": True,
            "message": "amount mismatch",
            "expected": expected,
            "got": amount,
            "ma_hd": ma_hd
        }), 200

    hoa_don.trangThai = TrangThaiHoaDonEnum.DA_THANH_TOAN
    hoa_don.ngayThanhToan = datetime.datetime.now()
    exists = (ThongBao.query
              .filter(ThongBao.hoaDon_id == hoa_don.id)
              .filter(ThongBao.is_read == False)
              .filter(ThongBao.message.ilike("%Online%"))
              .first())

    if not exists:
        tb = ThongBao(
            hoaDon_id=hoa_don.id,
            is_read=False,
            message=f"Đơn Online #{hoa_don.maThamChieu or ('HD' + str(hoa_don.id))} đã thanh toán"
        )
        db.session.add(tb)

    db.session.commit()

    print(f"[SePay] CONFIRMED {ma_hd} amount={amount}")
    return jsonify({"ok": True, "message": "Payment confirmed", "ma_hd": ma_hd}), 200




def vietqr_quicklink(amount: int, add_info: str) -> str:
    add_info = urllib.parse.quote(add_info)
    return (
        f"https://api.vietqr.io/image/{BANK_ACQ_ID}-{BANK_ACCOUNT_NO}-{VIETQR_TEMPLATE_ID}.jpg"
        f"?amount={int(amount)}&addInfo={add_info}&accountName={urllib.parse.quote(BANK_ACCOUNT_NAME)}"
    )


@app.route("/payment/qr/<int:hoa_don_id>", methods=["GET"])
def payment_qr(hoa_don_id):
    hd = HoaDon.query.get_or_404(hoa_don_id)

    # đảm bảo có mã tham chiếu
    if not hd.maThamChieu:
        hd.maThamChieu = f"HD{hd.id}"
        db.session.commit()


    if hd.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN:
        return redirect(url_for("payment_success", hoa_don_id=hd.id))

    # Chỉ tạo QR khi đang chờ thanh toán
    if hd.trangThai != TrangThaiHoaDonEnum.CHO_THANH_TOAN:
        abort(400)

    qr_url = vietqr_quicklink(amount=int(hd.tongThanhToan), add_info=hd.maThamChieu)
    return render_template("payment_qr.html", hoa_don=hd, qr_url=qr_url)


@app.route("/payment/status/<int:hoa_don_id>")
def payment_status(hoa_don_id):
    hd = HoaDon.query.get_or_404(hoa_don_id)
    return jsonify({
        "status": hd.trangThai.value
    })


@app.route("/payment/success/<int:hoa_don_id>")
def payment_success(hoa_don_id):
    hd = HoaDon.query.get_or_404(hoa_don_id)
    return render_template("payment_success.html", hoa_don=hd)




@app.route("/admin")
def admin_dashboard():
    if session.get('role') not in ['QUAN_LY_CUA_HANG', 'QUAN_LY_KHO']:
        return redirect(url_for('login'))
    return redirect("/admin/")  # Flask-Admin default index


@login.user_loader
def load_user(user_id):
    u = NhanVienCuaHang.query.get(int(user_id))
    if not u:
        return None

    try:
        if u.trangThai == TrangThaiEnum.INACTIVE:
            return None
    except Exception:
        return None

    return u

# ====== NHÂN VIÊN - POS

@app.route("/pos")
@login_required
def pos_page():
    role_str = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_str != "NHAN_VIEN":
        return redirect(url_for("login_my_user"))

    pos_order_type = session.get("pos_order_type", "TAI_QUAN")

    # ===== FILTER + PAGINATION PARAMS =====
    page = request.args.get("page", 1, type=int)
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "ALL").strip()

    # ===== QUERY + PAGINATE (DÙNG HÀM CHUNG) =====
    pagination = query_mon_list(q=q, category=category).paginate(
        page=page,
        per_page=PAGE_SIZE,
        error_out=False
    )

    items = pagination.items
    pages = pagination.pages

    # ===== GIỎ POS =====
    pos_cart = session.get("pos_cart", {}) or {}
    open_customer_modal = bool(session.pop("open_customer_modal", False))
    session.modified = True

    # ===== MODAL OVERLAY (nếu có mon_id) =====
    mon_id = request.args.get("mon_id", type=int)
    edit_key = (request.args.get("edit_key") or "").strip()
    modal_ctx = None

    if mon_id:
        mon = Mon.query.get_or_404(mon_id)
        if mon.loaiMon != LoaiMonEnum.NUOC:
            pos_cart = session.get("pos_cart", {}) or {}

            option_key = f"{mon.id}|NOOPT"

            resp = check_cart_limit_or_redirect(
                cart=pos_cart,
                option_key=option_key,
                redirect_endpoint="pos_page",
                redirect_kwargs={"page": page, "q": q, "category": category},
                message="Quá số lượng món trên hóa đơn (tối đa 10 món khác nhau).",
                edit_key=None
            )
            if resp:
                return resp

            if option_key not in pos_cart:
                pos_cart[option_key] = {
                    "id": mon.id,
                    "name": mon.name,
                    "price": float(mon.gia),
                    "quantity": 0,
                    "options": None
                }

            pos_cart[option_key]["quantity"] += 1
            session["pos_cart"] = pos_cart
            session.modified = True

            return redirect(url_for("pos_page", page=page, q=q, category=category))

        if mon.loaiMon == LoaiMonEnum.NUOC:
            SIZE_OPTS, SUGAR_OPTS, ICE_OPTS = get_drink_static_opts()
            TOPPING_OPTS = get_topping_opts_for_mon(mon)

            form = {"size": "S", "duong": "70", "da": "70", "topping": [], "note": "", "quantity": "1"}

            if edit_key and edit_key in pos_cart:
                old = pos_cart[edit_key]
                opts = old.get("options", {}) or {}
                form = {
                    "size": opts.get("size", "S"),
                    "duong": str(opts.get("duong", "70")),
                    "da": str(opts.get("da", "70")),
                    "topping": opts.get("topping", []),
                    "note": opts.get("note", ""),
                    "quantity": str(old.get("quantity", 1))
                }

            form["topping"] = normalize_topping_codes(form["topping"], TOPPING_OPTS)

            unit_price, desc_list = build_drink(mon, form["size"], form["duong"], form["da"], form["topping"])
            qty = int(form["quantity"] or 1)
            total_price = unit_price * qty

            modal_ctx = dict(
                mon=mon,
                form=form,
                errors={},
                unit_price=unit_price,
                total_price=total_price,
                desc_list=desc_list,
                SIZE_OPTS=SIZE_OPTS,
                SUGAR_OPTS=SUGAR_OPTS,
                ICE_OPTS=ICE_OPTS,
                TOPPING_OPTS=TOPPING_OPTS,
                edit_key=edit_key or None,
                ui_mode="MENU",
                close_url=url_for("pos_page", page=page, q=q, category=category),
                form_action=url_for("pos_drink_config", mon_id=mon.id)
            )

    resp = make_response(render_template(
        "pos.html",
        items=items,
        pos_cart=pos_cart,
        modal_ctx=modal_ctx,
        page=page,
        pages=pages,
        q=q,
        category=category,
        pos_order_type=pos_order_type,
        open_customer_modal=open_customer_modal
    ))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

def get_pos_cart():
    return session.get("pos_cart", {}) or {}


def save_pos_cart(cart: dict):
    session["pos_cart"] = cart
    session.modified = True


@app.route("/pos/drink/<int:mon_id>", methods=["GET", "POST"])
@login_required
def pos_drink_config(mon_id):
    mon = Mon.query.get_or_404(mon_id)

    # Nếu không phải NUOC -> add nhanh 1 cái (giữ đúng logic hiện tại)
    if mon.loaiMon != LoaiMonEnum.NUOC:
        cart = get_pos_cart()
        option_key = f"{mon.id}|NOOPT"

        resp = check_cart_limit_or_redirect(
            cart=cart,
            option_key=option_key,
            redirect_endpoint="pos_page",
            redirect_kwargs={},
            message="Quá số lượng món trên hóa đơn (tối đa 10 món khác nhau).",
            edit_key=None
        )
        if resp:
            return resp

        if option_key not in cart:
            cart[option_key] = {
                "id": mon.id,
                "name": mon.name,
                "price": float(mon.gia),
                "quantity": 0,
                "options": None
            }

        cart[option_key]["quantity"] += 1
        save_pos_cart(cart)
        return redirect(url_for("pos_page"))

    SIZE_OPTS, SUGAR_OPTS, ICE_OPTS = get_drink_static_opts()
    TOPPING_OPTS = get_topping_opts_for_mon(mon)

    # ====== GET ======
    if request.method == "GET":
        cart = get_pos_cart()
        edit_key = (request.args.get("edit_key") or "").strip()

        form = get_drink_form_defaults(cart, edit_key)
        form["topping"] = normalize_topping_codes(form.get("topping", []), TOPPING_OPTS)

        unit_price, desc_list = build_drink(mon, form["size"], form["duong"], form["da"], form["topping"])
        try:
            qty = int(form.get("quantity") or 1)
        except:
            qty = 1
        total_price = unit_price * max(qty, 1)

        return render_template(
            "drink_modal.html",
            mon=mon,
            form=form,
            errors={},
            unit_price=unit_price,
            total_price=total_price,
            desc_list=desc_list,
            SIZE_OPTS=SIZE_OPTS,
            SUGAR_OPTS=SUGAR_OPTS,
            ICE_OPTS=ICE_OPTS,
            TOPPING_OPTS=TOPPING_OPTS,
            edit_key=edit_key or None,

            # override cho POS
            close_url=url_for("pos_page"),
            form_action=url_for("pos_drink_config", mon_id=mon.id),
            ui_mode="MENU"
        )

    # ====== POST ======
    size = (request.form.get("size") or "S").strip()
    duong = (request.form.get("duong") or "70").strip()
    da = (request.form.get("da") or "70").strip()
    topping = request.form.getlist("topping")
    note = (request.form.get("note") or "").strip()
    qty_raw = (request.form.get("quantity") or "1").strip()
    edit_key = (request.form.get("edit_key") or "").strip()
    action = (request.form.get("action") or "").strip()

    topping = normalize_topping_codes(topping, TOPPING_OPTS)

    errors = {}
    try:
        qty = int(qty_raw)
        if qty < 1:
            raise ValueError()
    except:
        errors["quantity"] = "Số lượng không hợp lệ."
        qty = 1

    unit_price, desc_list = build_drink(mon, size, duong, da, topping)
    total_price = unit_price * qty

    if action != "add" or errors:
        form = {
            "size": size,
            "duong": duong,
            "da": da,
            "topping": topping,
            "note": note,
            "quantity": qty_raw
        }
        return render_template(
            "drink_modal.html",
            mon=mon,
            form=form,
            errors=errors,
            unit_price=unit_price,
            total_price=total_price,
            desc_list=desc_list,
            SIZE_OPTS=SIZE_OPTS,
            SUGAR_OPTS=SUGAR_OPTS,
            ICE_OPTS=ICE_OPTS,
            TOPPING_OPTS=TOPPING_OPTS,
            edit_key=edit_key or None,

            close_url=url_for("pos_page"),
            form_action=url_for("pos_drink_config", mon_id=mon.id),
            ui_mode="MENU"
        )

    # ====== Add/Update POS cart (dùng service trong dao.py) ======
    cart = get_pos_cart()

    option_key = make_drink_option_key(mon.id, size, duong, da, topping, note)

    resp = check_cart_limit_or_redirect(
        cart=cart,
        option_key=option_key,
        redirect_endpoint="pos_page",
        redirect_kwargs={},
        message="Quá số lượng món trên hóa đơn (tối đa 10 món khác nhau).",
        edit_key=edit_key
    )
    if resp:
        return resp

    cart, _, _, _, _ = upsert_drink_to_cart(
        cart=cart,
        mon=mon,
        size=size,
        duong=duong,
        da=da,
        toppings=topping,
        note=note,
        qty_raw=qty_raw,
        edit_key=edit_key
    )

    save_pos_cart(cart)
    return redirect(url_for("pos_page"))



@app.route("/pos/cart/inc/<path:key>", methods=["POST"])
@login_required
def pos_cart_inc(key):
    key = unquote(key)
    cart = session.get("pos_cart", {}) or {}
    if key in cart:
        cart[key]["quantity"] = int(cart[key].get("quantity", 0)) + 1
        session["pos_cart"] = cart
        session.modified = True

    page = request.form.get("page", type=int) or 1
    return redirect(url_for("pos_page", page=page))


@app.route("/pos/cart/dec/<path:key>", methods=["POST"])
@login_required
def pos_cart_dec(key):
    key = unquote(key)
    cart = session.get("pos_cart", {}) or {}
    if key in cart:
        q = int(cart[key].get("quantity", 0)) - 1
        if q <= 0:
            cart.pop(key, None)
        else:
            cart[key]["quantity"] = q
        session["pos_cart"] = cart
        session.modified = True

    page = request.form.get("page", type=int) or 1
    return redirect(url_for("pos_page", page=page))


@app.route("/pos/cart/clear", methods=["POST"])
@login_required
def pos_cart_clear():
    session.pop("pos_cart", None)
    session.modified = True
    return redirect(url_for("pos_page"))


@app.route("/pos/cart/remove/<path:key>", methods=["POST"])
@login_required
def pos_cart_remove(key):
    key = unquote(key)
    cart = session.get("pos_cart", {}) or {}
    cart.pop(key, None)
    session["pos_cart"] = cart
    session.modified = True

    page = request.form.get("page", type=int) or 1
    return redirect(url_for("pos_page", page=page))


@app.post("/pos/customer/save")
def pos_customer_save():
    name = (request.form.get("customer_name") or "").strip()
    phone = (request.form.get("customer_phone") or "").strip().replace(" ", "")
    page = request.form.get("page", 1)

    if not PHONE_RE.match(phone):
        session["customer_err"] = "Vui lòng nhập số điện thoại hợp lệ (10 số, bắt đầu bằng 0)."
        session["open_customer_modal"] = True
        session.modified = True
        return redirect(url_for("pos_page", page=page))

    session["pos_customer"] = {"name": name, "phone": phone}
    session.modified = True
    return redirect(url_for("pos_page", page=page))


@app.post("/pos/customer/clear")
def pos_customer_clear():
    page = request.form.get("page", 1)
    session.pop("pos_customer", None)
    session.modified = True
    return redirect(url_for("pos_page", page=page))


@app.post("/pos/order-type")
@login_required
def pos_set_order_type():
    v = (request.form.get("order_type") or "TAI_QUAN").strip()
    page = request.form.get("page", 1, type=int) or 1

    allowed = {"TAI_QUAN", "MANG_DI"}
    if v not in allowed:
        v = "TAI_QUAN"

    session["pos_order_type"] = v
    session.modified = True
    return redirect(url_for("pos_page", page=page))



@app.route("/pos/service-fee", methods=["POST"])
@login_required
def pos_set_service_fee():
    v = (request.form.get("service_percent", "0") or "0").strip()

    try:
        # chỉ cho 0..100
        percent = float(v)
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
    except:
        percent = 0

    session["pos_service_percent"] = percent
    session.modified = True

    return redirect(url_for("pos_page"))


@app.route("/pos/print-temp")
@login_required
def pos_print_temp():
    hd, payload = upsert_hoa_don_from_pos_cart(
        TrangThaiHoaDonEnum.CHO_THANH_TOAN,
        rebuild_details=True
    )
    if not hd:
        return render_template("pos_print_temp.html", empty_cart=True)

    items, meta = payload
    items = normalize_items(items)

    khach = KhachHang.query.get(hd.khachHang_id) if hd.khachHang_id else None

    meta.pop("khach", None)
    return render_template(
        "pos_print_temp.html",
        empty_cart=False,
        bill=hd,
        items=items,
        khach=khach,
        **meta
    )


@app.post("/pos/pay")
@login_required
def pos_pay():
    hd, items, meta = pay_from_pos_cart(rebuild_details=True)
    if not hd:
        return redirect(url_for("pos_page"))

    # clear giỏ pos sau khi chốt bill
    session.pop("pos_cart", None)
    session.pop("pos_current_bill_id", None)
    session.modified = True

    return redirect(url_for("pos_print_final", bill_id=hd.id))



@app.get("/pos/print/final/<int:bill_id>")
@login_required
def pos_print_final(bill_id):
    hd = HoaDon.query.get_or_404(bill_id)

    cts = ChiTietHoaDon.query.filter_by(hoaDon_id=hd.id).all()

    items = []
    subtotal = 0
    total_qty = 0
    for ct in cts:
        ten_mon = ct.mon.name if getattr(ct, "mon", None) else f"Món #{ct.mon_id}"
        line_total = (ct.soLuong or 0) * (ct.donGia or 0)
        items.append({"ten": ten_mon, "sl": ct.soLuong or 0, "tien": line_total})
        subtotal += line_total
        total_qty += (ct.soLuong or 0)

    tax_rate = 0.08
    tax_amount = subtotal * tax_rate
    service_percent = int(getattr(hd, "service_percent", 0) or 0)
    service_fee = subtotal * (service_percent / 100.0) if service_percent > 0 else 0
    grand_total = subtotal + tax_amount + service_fee

    meta = {
        "subtotal": subtotal,
        "total_qty": total_qty,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "service_percent": service_percent,
        "service_fee": service_fee,
        "grand_total": grand_total,
        "now": datetime.datetime.now(),
    }


    khach = KhachHang.query.get(hd.khachHang_id) if hd.khachHang_id else None
    meta.pop("khach", None)


    qr_uri = None
    if hd.loaiHoaDon == LoaiDungEnum.TAI_QUAN:
        qr = QRCode.query.filter_by(
            hoaDon_id=hd.id,
            loaiQR=LoaiQREnum.NHAP_SO_BAN,
            trangThai=TrangThaiQREnum.CON_HIEU_LUC
        ).first()
        if qr:
            full_url = request.host_url.rstrip("/") + qr.noiDungQR
            qr_uri = make_qr_data_uri(full_url)

    return render_template(
        "pos_print_final.html",
        empty_cart=False,
        hd=hd,
        items=items,
        khach=khach,
        qr_uri=qr_uri,
        **meta
    )


@app.route("/enter-table/<ma_qr>", methods=["GET", "POST"])
def enter_table(ma_qr):
    # GET: chỉ render form (có thể show hóa đơn nếu muốn)
    if request.method == "POST":
        raw = (request.form.get("so_ban") or "").strip()
        try:
            so_ban = int(raw)
        except:
            so_ban = 0

        if so_ban <= 0:
            return render_template("enter_table.html", hoa_don=None, error="Vui lòng nhập số bàn hợp lệ.")

        confirm_table_by_qr(ma_qr, so_ban)

        # đưa khách về trang chủ quán
        return redirect(url_for("index"))

    # GET: giữ code cũ nếu bạn cần show hoa_don
    qr = QRCode.query.filter_by(
        maQR=ma_qr,
        loaiQR=LoaiQREnum.NHAP_SO_BAN,
        trangThai=TrangThaiQREnum.CON_HIEU_LUC
    ).first_or_404()
    hd = HoaDon.query.get_or_404(qr.hoaDon_id)

    if hd.loaiHoaDon != LoaiDungEnum.TAI_QUAN:
        return "QR không hợp lệ cho hóa đơn mang đi.", 400

    return render_template("enter_table.html", hoa_don=hd, error=None)



@app.get("/pos/api/notifications")
@login_required
def pos_api_notifications():
    role_str = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_str != "NHAN_VIEN":
        return jsonify({"ok": False}), 403

    notis = (ThongBao.query
             .filter_by(is_read=False)
             .order_by(ThongBao.created_at.desc())
             .limit(20)
             .all())

    data = []
    for tb in notis:
        data.append({
            "id": tb.id,
            "message": tb.message,
            "time": tb.created_at.strftime("%d/%m %H:%M"),
            "hoaDonId": tb.hoaDon_id
        })

    return jsonify({
        "ok": True,
        "count": len(data),
        "items": data
    })


@app.get("/pos/notifications/open/<int:noti_id>")
@login_required
def pos_open_notification(noti_id):
    role_str = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_str != "NHAN_VIEN":
        return redirect(url_for("login_my_user"))

    tb = ThongBao.query.get_or_404(noti_id)
    tb.is_read = True
    db.session.commit()

    return redirect(url_for("print_kitchen_bill", bill_id=tb.hoaDon_id))


@app.route("/pos/print/kitchen/<int:bill_id>" , methods = ["get"])
def print_kitchen_bill(bill_id):
    hd = (HoaDon.query
          .options(
              joinedload(HoaDon.chiTiet).joinedload(ChiTietHoaDon.mon),
              joinedload(HoaDon.chiTiet)
                  .joinedload(ChiTietHoaDon.topping_links)
                  .joinedload(ChiTietHoaDonTopping.topping),
              joinedload(HoaDon.khachHang),
          )
          .get_or_404(bill_id))

    items = hd.chiTiet or []
    return render_template("pos_print_kitchen.html", hd=hd, items=items)




@app.route("/pos/order-history", endpoint="order_history")
@login_required
def pos_order_history():
    role_str = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_str != "NHAN_VIEN":
        return redirect(url_for("login_my_user"))

    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)

    base = (
        HoaDon.query
        .options(
            selectinload(HoaDon.khachHang),
            selectinload(HoaDon.chiTiet).selectinload(ChiTietHoaDon.mon),
        )
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .order_by(HoaDon.ngayThanhToan.desc())
    )

    if q:
        base = base.outerjoin(KhachHang).filter(
            or_(
                HoaDon.maThamChieu.ilike(f"%{q}%"),
                KhachHang.sdt.ilike(f"%{q}%"),
            )
        )

    pagination = base.paginate(page=page, per_page=PAGE_SIZE, error_out=False)
    bills = pagination.items

    orders = []
    for hd in bills:
        kh = hd.khachHang
        kh_ten = kh.name if kh else ""
        kh_sdt = kh.sdt if kh else ""

        items = []
        item_count = 0
        for ct in (hd.chiTiet or []):
            qty = ct.soLuong or 0
            price = ct.donGia or 0
            item_count += qty
            mon_name = ct.mon.name if ct.mon else ""
            items.append({"name": mon_name, "qty": qty, "price": price})

        orders.append({
            "id": hd.id,
            "ma": hd.maThamChieu or f"HD{hd.id}",
            "order_type": hd.loaiHoaDon.value if hasattr(hd.loaiHoaDon, "value") else str(hd.loaiHoaDon),
            "khach_ten": kh_ten,
            "khach_sdt": kh_sdt,
            "paid_at": hd.ngayThanhToan,
            "total": hd.tongThanhToan or 0,
            "item_count": item_count,
            "items": items,
        })

    return render_template(
        "order_history.html",
        orders=orders,
        pagination=pagination,
        page=page,
        q=q
    )




@app.route('/check-in', methods=['GET', 'POST'])
def check_in_table():
    if request.method == 'POST':
        so_ban = request.form.get('table_number')
        if so_ban:
            return redirect(url_for('index'))
    return render_template('enter_table.html')




# Noti BOT
@app.route("/admin/kho/noti/count", methods =['get'])
def kho_noti_count():
    if not current_user.is_authenticated:
        return jsonify({"count": 0})

    role = getattr(current_user.role, "value", None) or str(current_user.role)
    if role != "QUAN_LY_KHO":
        return jsonify({"count": 0})

    return jsonify({"count": count_unread_thong_bao_kho()})


@app.route("/admin/kho/noti/list", methods = ['get'])
def kho_noti_list():
    if not current_user.is_authenticated:
        return jsonify([])

    role = getattr(current_user.role, "value", None) or str(current_user.role)
    if role != "QUAN_LY_KHO":
        return jsonify([])

    items = get_latest_thong_bao_kho(10)

    return jsonify([{
        "id": x.id,
        "message": x.message,
        "created_at": x.created_at.strftime("%d/%m %H:%M"),
        "unread": x.trang_thai.name == "UNREAD",
        "nguyenLieu_id": x.nguyenLieu_id
    } for x in items])


@app.route("/admin/kho/noti/open/<int:noti_id>", methods = ['get'])
def kho_noti_open(noti_id):
    if not current_user.is_authenticated:
        return redirect(url_for("login_my_user"))

    role = getattr(current_user.role, "value", None) or str(current_user.role)
    if role != "QUAN_LY_KHO":
        return redirect(url_for("login_my_user"))

    n = mark_thong_bao_kho_as_read(noti_id)

    return redirect(
        url_for("phieu_nhap.index_view", nl_id=n.nguyenLieu_id or "")
    )


@app.route("/admin/kho/noti/delete/<int:noti_id>", methods = ['post'])
def kho_noti_delete(noti_id):
    if not current_user.is_authenticated:
        return jsonify({"ok": False})

    role = getattr(current_user.role, "value", None) or str(current_user.role)
    if role != "QUAN_LY_KHO":
        return jsonify({"ok": False})

    delete_thong_bao_kho(noti_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    with app.app_context():
        app.run(host="0.0.0.0", port=5000, debug=True)



