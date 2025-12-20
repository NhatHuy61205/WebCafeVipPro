
import hashlib
import secrets
from flask import abort
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple
import datetime as dt
from sqlalchemy import func

from CafeApp import db, app
from flask import session
from CafeApp.models import NhanVienCuaHang, SizeEnum, Topping, MonTopping, TrangThaiHoaDonEnum, ChiTietHoaDon, \
    LoaiDungEnum, HoaDon, ChiTietHoaDonTopping, KhachHang, LoaiQREnum, TrangThaiQREnum, QRCode, ThongBao, Mon, \
    NguyenLieu, NhomNguyenLieuEnum


@dataclass
class DrinkContext:
    name: str
    base_price: float
    desc: List[str]

class DrinkComponent:
    def get_price(self) -> float:
        raise NotImplementedError

    def get_desc(self) -> List[str]:
        raise NotImplementedError

class BaseDrink(DrinkComponent):
    def __init__(self, name: str, base_price: float):
        self.ctx = DrinkContext(name=name, base_price=base_price, desc=[])

    def get_price(self) -> float:
        return self.ctx.base_price

    def get_desc(self) -> List[str]:
        return list(self.ctx.desc)

class DrinkDecorator(DrinkComponent):
    def __init__(self, component: DrinkComponent):
        self.component = component

    def get_price(self) -> float:
        return self.component.get_price()

    def get_desc(self) -> List[str]:
        return self.component.get_desc()

class SizeDecorator(DrinkDecorator):
    # S: +0, M: +5000, L: +10000
    PRICE = {"S": 0, "M": 5000, "L": 10000}
    LABEL = {"S": "Size S", "M": "Size M (+5k)", "L": "Size L (+10k)"}

    def __init__(self, component: DrinkComponent, size: str):
        super().__init__(component)
        self.size = size if size in self.PRICE else "S"

    def get_price(self) -> float:
        return super().get_price() + self.PRICE[self.size]

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.size]]

class SugarDecorator(DrinkDecorator):
    LABEL = {"0": "0% đường", "30": "30% đường", "50": "50% đường", "70": "70% đường", "100": "100% đường"}

    def __init__(self, component: DrinkComponent, sugar: str):
        super().__init__(component)
        self.sugar = sugar if sugar in self.LABEL else "70"

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.sugar]]

class IceDecorator(DrinkDecorator):
    LABEL = {"0": "0% đá", "50": "50% đá", "70": "70% đá", "100": "100% đá"}

    def __init__(self, component: DrinkComponent, ice: str):
        super().__init__(component)
        self.ice = ice if ice in self.LABEL else "70"

    def get_desc(self) -> List[str]:
        return super().get_desc() + [self.LABEL[self.ice]]

class ToppingDecorator:
    def __init__(self, drink, topping_code: str, topping_name: str = None, topping_price: float = 0.0):
        self.drink = drink
        self.topping_code = topping_code
        self.topping_name = topping_name or topping_code
        self.topping_price = float(topping_price or 0)

    def get_price(self):
        return self.drink.get_price() + self.topping_price

    def get_desc(self):
        return self.drink.get_desc() + [f"Topping: {self.topping_name} (+{int(self.topping_price):,}đ)"]

def build_drink(mon, size: str, duong: str, da: str, toppings: List[str]):
    drink = BaseDrink(name=mon.name, base_price=float(mon.gia))
    drink = SizeDecorator(drink, size)
    drink = SugarDecorator(drink, duong)
    drink = IceDecorator(drink, da)


    allowed_map = {}
    for link in getattr(mon, "allowed_toppings", []) or []:
        t = link.topping
        if not t or not getattr(t, "is_active", True):
            continue
        price = link.override_price if link.override_price is not None else t.price
        allowed_map[t.code] = {
            "name": t.name,
            "price": float(price or 0)
        }

    for code in toppings:
        if code in allowed_map:
            info = allowed_map[code]
            drink = ToppingDecorator(drink, code, info["name"], info["price"])

    unit_price = drink.get_price()
    desc_list = drink.get_desc()
    return unit_price, desc_list

def get_drink_static_opts():
    """Các option không phụ thuộc DB (size/đường/đá)."""
    SIZE_OPTS = [("S", "Nhỏ", 0), ("M", "Vừa", 5000), ("L", "Lớn", 10000)]
    SUGAR_OPTS = [("0", "0%"), ("30", "30%"), ("50", "50%"), ("70", "70%"), ("100", "100%")]
    ICE_OPTS = [("0", "0%"), ("50", "50%"), ("70", "70%"), ("100", "100%")]
    return SIZE_OPTS, SUGAR_OPTS, ICE_OPTS


def get_topping_opts_for_mon(mon):

    opts = []
    for link in getattr(mon, "allowed_toppings", []) or []:
        t = link.topping
        if not t or not getattr(t, "is_active", True):
            continue
        price = link.override_price if link.override_price is not None else t.price
        opts.append((t.code, t.name, int(price)))

    opts.sort(key=lambda x: x[1])
    return opts


def normalize_topping_codes(selected_codes, topping_opts):
    allowed = {code for code, _, _ in topping_opts}
    return [c for c in selected_codes if c in allowed]

# def auth_user(username, password):
#     password = hashlib.md5(password.encode("utf-8")).hexdigest()
#     return NhanVienCuaHang.query.filter(
#         NhanVienCuaHang.tenDangNhap == username,
#         NhanVienCuaHang.matKhau == password
#     ).first()

def auth_user(username, password):
    return NhanVienCuaHang.query.filter(
        NhanVienCuaHang.tenDangNhap == username,
        NhanVienCuaHang.matKhau == password
    ).first()



def _next_walkin_phone(prefix="000"):
    last = KhachHang.query.filter(KhachHang.name == "Khách lẻ").order_by(KhachHang.id.desc()).first()
    if last and last.sdt and last.sdt.isdigit():
        n = int(last.sdt)
    else:
        n = 0
    n += 1
    return str(n).zfill(10)

def get_or_create_khach_hang_from_pos():

    raw = session.get("pos_customer") or {}

    ten = (raw.get("name") or raw.get("ten") or raw.get("tenKhach") or "").strip()
    sdt = (raw.get("phone") or raw.get("sdt") or raw.get("soDienThoai") or "").strip()
    dia_chi = (raw.get("diaChi") or raw.get("address") or "").strip()

    # mặc định POS: tại quán
    if not dia_chi:
        dia_chi = "Tại quán"


    if not ten and not sdt:
        sdt_auto = _next_walkin_phone()
        kh = KhachHang(
            name="Khách lẻ",
            sdt=sdt_auto,
            diaChi=dia_chi,
            loaiKhachHang=LoaiDungEnum.TAI_QUAN,
        )
        db.session.add(kh)
        db.session.commit()
        return kh


    if sdt:
        kh = KhachHang.query.filter_by(sdt=sdt).first()
        if kh:
            # update tên/địa chỉ nếu người dùng nhập
            if ten and kh.name != ten:
                kh.name = ten
            if dia_chi and kh.diaChi != dia_chi:
                kh.diaChi = dia_chi

            if hasattr(kh, "loaiKhachHang"):
                kh.loaiKhachHang = LoaiDungEnum.TAI_QUAN
            db.session.commit()
            return kh


        kh = KhachHang(
            name=ten or "Khách lẻ",
            sdt=sdt,
            diaChi=dia_chi,
            loaiKhachHang=LoaiDungEnum.TAI_QUAN,
        )
        db.session.add(kh)
        db.session.commit()
        return kh


    sdt_auto = _next_walkin_phone()
    kh = KhachHang(
        name=ten,
        sdt=sdt_auto,
        diaChi=dia_chi,
        loaiKhachHang=LoaiDungEnum.TAI_QUAN,
    )
    db.session.add(kh)
    db.session.commit()
    return kh



# ===== DRINK FORM / CART SERVICE (DÙNG CHUNG MENU + POS) =====

def parse_int(value, default=1, min_v=1):
    try:
        n = int(str(value).strip())
    except:
        n = default
    if n < min_v:
        n = min_v
    return n


def get_drink_form_defaults(cart: dict, edit_key: str = "") -> dict:
    form = {"size": "S", "duong": "70", "da": "70", "topping": [], "note": "", "quantity": "1"}

    edit_key = (edit_key or "").strip()
    if edit_key and cart and edit_key in cart:
        old = cart.get(edit_key, {}) or {}
        opts = old.get("options", {}) or {}
        form = {
            "size": (opts.get("size") or "S"),
            "duong": str(opts.get("duong") or "70"),
            "da": str(opts.get("da") or "70"),
            "topping": opts.get("topping") or [],
            "note": opts.get("note") or "",
            "quantity": str(old.get("quantity") or 1),
        }
    return form


def make_drink_option_key(mon_id: int, size: str, duong: str, da: str, toppings: list, note: str) -> str:
    size = (size or "S").strip()
    duong = (duong or "70").strip()
    da = (da or "70").strip()
    note = (note or "").strip()
    toppings = toppings or []
    return f"{mon_id}|{size}|{duong}|{da}|{','.join(sorted(toppings))}|{note}"


def upsert_drink_to_cart(
    cart: dict,
    mon,
    size: str,
    duong: str,
    da: str,
    toppings: list,
    note: str,
    qty_raw,
    edit_key: str = "",
):

    cart = cart or {}

    TOPPING_OPTS = get_topping_opts_for_mon(mon)
    toppings = normalize_topping_codes(toppings or [], TOPPING_OPTS)

    qty = parse_int(qty_raw, default=1, min_v=1)

    unit_price, desc_list = build_drink(mon, size, duong, da, toppings)
    option_key = make_drink_option_key(mon.id, size, duong, da, toppings, note)

    edit_key = (edit_key or "").strip()
    if edit_key and edit_key in cart:
        cart.pop(edit_key, None)

    if option_key not in cart:
        cart[option_key] = {
            "id": mon.id,
            "name": mon.name,
            "price": float(unit_price),
            "quantity": 0,
            "options": {
                "size": (size or "S").strip(),
                "duong": (duong or "70").strip(),
                "da": (da or "70").strip(),
                "topping": toppings,
                "note": (note or "").strip(),
                "desc": desc_list,
            },
        }

    cart[option_key]["quantity"] += qty
    return cart, option_key, unit_price, desc_list, qty


# Lưu Hóa Đơn

def _coerce_size(size_val):
    # size_val có thể là "S"/"M"/"L" hoặc "SizeEnum.S"
    if not size_val:
        return SizeEnum.S
    if isinstance(size_val, SizeEnum):
        return size_val
    s = str(size_val).strip().upper()
    if s in ("S", "M", "L"):
        return SizeEnum[s]
    return SizeEnum.S

def _resolve_topping_ids(topping_list):
    if not topping_list:
        return []

    ids = []
    for t in topping_list:
        if t is None:
            continue

        if isinstance(t, int):
            ids.append(t)
            continue

        ts = str(t).strip()
        if not ts:
            continue

        top = Topping.query.filter_by(code=ts).first()
        if not top:
            top = Topping.query.filter_by(name=ts).first()

        if top:
            ids.append(top.id)


    seen = set()
    out = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _topping_price_at_time(mon_id: int, topping_id: int):

    link = MonTopping.query.filter_by(mon_id=mon_id, topping_id=topping_id).first()
    if link and link.override_price is not None:
        return int(link.override_price)

    top = Topping.query.get(topping_id)
    return int(top.price) if top else 0


def upsert_hoa_don_from_pos_cart(
    status: TrangThaiHoaDonEnum,
    rebuild_details: bool = False
):

    cart = session.get("pos_cart") or {}
    if not cart:
        return None, None

    # ===== TÍNH TIỀN TỪ GIỎ =====
    total_qty = 0
    subtotal = 0.0
    items = []

    for key, it in cart.items():
        qty = int(it.get("quantity", 0) or 0)
        price = float(it.get("price", 0) or 0)

        opt = it.get("options") or {}
        has_opt = bool(opt.get("size") or opt.get("duong") or opt.get("da") or opt.get("topping"))
        size = _coerce_size(opt.get("size")) if has_opt else None
        muc_duong = int(opt.get("duong", opt.get("mucDuong", 100)) or 100) if has_opt else None
        muc_da = int(opt.get("da", opt.get("mucDa", 100)) or 100) if has_opt else None
        topping_raw = opt.get("topping") or []
        note = (opt.get("note") or "").strip()

        total_qty += qty
        subtotal += price * qty

        items.append({
            "key": key,
            "mon_id": it.get("id"),
            "name": it.get("name", ""),
            "qty": qty,
            "unit_price": price,
            "line_total": price * qty,
            "size": size,
            "mucDuong": muc_duong,
            "mucDa": muc_da,
            "note": note,
            "topping_ids": _resolve_topping_ids(topping_raw),
        })

    apply_tax = bool(session.get("apply_tax", True))
    tax_rate = 0.08 if apply_tax else 0.0
    tax_amount = subtotal * tax_rate

    service_percent = float(session.get("pos_service_percent") or 0)
    service_fee = subtotal * (service_percent / 100.0)

    grand_total = subtotal + tax_amount + service_fee

    # ===== LOẠI HÓA ĐƠN =====
    loai_str = (session.get("pos_order_type") or "TAI_QUAN").strip()
    if loai_str not in LoaiDungEnum.__members__:
        loai_str = "TAI_QUAN"
    loai_enum = LoaiDungEnum[loai_str]

    kh = get_or_create_khach_hang_from_pos()
    kh_id = kh.id

    bill_id = session.get("pos_current_bill_id")
    hd = HoaDon.query.get(bill_id) if bill_id else None

    # ===== TẠO MỚI / UPDATE =====
    if not hd:
        # HoaDon kế thừa Base => có field name NOT NULL (theo ảnh Base)
        hd = HoaDon(
            name="HOA_DON",
            ngayTao= datetime.now(),
            ngayThanhToan=None,
            soBan=session.get("pos_table_no"),
            tongTienHang=subtotal,
            thue=tax_amount,
            phiPhucVu=service_fee,
            giamGia=0.0,
            tongThanhToan=grand_total,
            loaiHoaDon=loai_enum,
            trangThai=status,
            khachHang_id=kh_id,
        )
        db.session.add(hd)
        db.session.flush()  # lấy hd.id

        # update name đẹp (tùy bạn)
        hd.name = f"HD-{hd.id}"

        # tạo chi tiết + topping
        for it in items:
            ct = ChiTietHoaDon(
                soLuong=it["qty"],
                donGia=it["unit_price"],
                thanhTien=it["line_total"],
                ghiChu=it["note"] or None,

                size=it["size"],
                mucDuong=it["mucDuong"],
                mucDa=it["mucDa"],

                hoaDon_id=hd.id,
                mon_id=int(it["mon_id"]),
            )
            db.session.add(ct)
            db.session.flush()  # lấy ct.id để add topping_links

            for top_id in it["topping_ids"]:
                link = ChiTietHoaDonTopping(
                    chi_tiet_hoa_don_id=ct.id,
                    topping_id=int(top_id),
                    qty=1,
                    price_at_time=_topping_price_at_time(int(it["mon_id"]), int(top_id)),
                )
                db.session.add(link)
        pos_type = session.get("pos_order_type", "TAI_QUAN")



        session["pos_current_bill_id"] = hd.id
        session.modified = True

    else:
        # nếu muốn rebuild chi tiết theo giỏ hiện tại
        if rebuild_details:
            # xóa từng ct để cascade delete topping_links (delete-orphan)
            for ct in list(hd.chiTiet):
                db.session.delete(ct)
            db.session.flush()

            for it in items:
                ct = ChiTietHoaDon(
                    soLuong=it["qty"],
                    donGia=it["unit_price"],
                    thanhTien=it["line_total"],
                    ghiChu=it["note"] or None,

                    size=it["size"],
                    mucDuong=it["mucDuong"],
                    mucDa=it["mucDa"],

                    hoaDon_id=hd.id,
                    mon_id=int(it["mon_id"]),
                )
                db.session.add(ct)
                db.session.flush()

                for top_id in it["topping_ids"]:
                    link = ChiTietHoaDonTopping(
                        chi_tiet_hoa_don_id=ct.id,
                        topping_id=int(top_id),
                        qty=1,
                        price_at_time=_topping_price_at_time(int(it["mon_id"]), int(top_id)),
                    )
                    db.session.add(link)

        # update tổng + trạng thái
        hd.khachHang_id = kh_id
        hd.tongTienHang = subtotal
        hd.thue = tax_amount
        hd.phiPhucVu = service_fee
        hd.tongThanhToan = grand_total
        hd.loaiHoaDon = loai_enum
        hd.trangThai = status

        if status == TrangThaiHoaDonEnum.DA_THANH_TOAN:
            hd.ngayThanhToan = datetime.now()

        db.session.commit()

    meta = {
        "total_qty": total_qty,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "service_percent": service_percent,
        "service_fee": service_fee,
        "grand_total": grand_total,
        "khach": kh,
        "now": datetime.now(),
    }
    return hd, (items, meta)


def pay_from_pos_cart(rebuild_details: bool = True):
    hd, pack = upsert_hoa_don_from_pos_cart(
        status=TrangThaiHoaDonEnum.DA_THANH_TOAN,
        rebuild_details=rebuild_details
    )
    if not hd:
        return None, None, None

    items, meta = pack

    # Nếu là TẠI QUÁN → tạo QR nhập số bàn
    if hd.loaiHoaDon == LoaiDungEnum.TAI_QUAN:
        token = secrets.token_urlsafe(16)

        qr = QRCode(
            maQR=token,
            loaiQR=LoaiQREnum.NHAP_SO_BAN,
            noiDungQR=f"/enter-table/{token}",
            hoaDon_id=hd.id,
            trangThai=TrangThaiQREnum.CON_HIEU_LUC
        )
        db.session.add(qr)

    db.session.commit()
    return hd, items, meta

def create_table_confirm_notification(hd, so_ban: int) -> ThongBao:
    kh = getattr(hd, "khachHang", None)
    if kh is None and getattr(hd, "khachHang_id", None):
        kh = KhachHang.query.get(hd.khachHang_id)

    ten = (getattr(kh, "name", None) or "Khách lẻ")
    sdt = (getattr(kh, "sdt", None) or "")

    msg = f"{ten}{(' - ' + sdt) if sdt else ''} | HĐ #{hd.id} đang ở bàn {so_ban}"

    tb = ThongBao(
        hoaDon_id=hd.id,
        message=msg,
        is_read=False,
        type="TABLE_CONFIRMED",
    )
    db.session.add(tb)
    return tb

def confirm_table_by_qr(ma_qr: str, so_ban: int):
    qr = QRCode.query.filter_by(
        maQR=ma_qr,
        loaiQR=LoaiQREnum.NHAP_SO_BAN,
        trangThai=TrangThaiQREnum.CON_HIEU_LUC
    ).first()

    if not qr:
        abort(404)

    hd = HoaDon.query.get(qr.hoaDon_id)
    if not hd:
        abort(404)

    if hd.loaiHoaDon != LoaiDungEnum.TAI_QUAN:
        abort(400, description="QR không hợp lệ cho hóa đơn mang đi.")

    if so_ban <= 0:
        abort(400, description="Số bàn không hợp lệ.")

    hd.soBan = so_ban
    qr.trangThai = TrangThaiQREnum.HET_HIEU_LUC

    # tạo thông báo
    create_table_confirm_notification(hd, so_ban)

    db.session.commit()
    return hd


# Báo cáo thống kê

def _start_of_week(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())  # Monday


def _month_range(d: dt.date):
    start = d.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1)
    else:
        end = start.replace(month=start.month + 1, day=1)
    return start, end


def dashboard_range(mode: str, raw_from: str = "", raw_to: str = ""):
    """Return: (mode, start_date, end_date_exclusive, time_label)"""
    mode = (mode or "WEEK").upper()
    today = dt.date.today()

    start_date = None
    end_date = None

    if mode == "TODAY":
        start_date = today
        end_date = today + dt.timedelta(days=1)
        time_label = today.strftime("%d/%m/%Y")

    elif mode == "MONTH":
        start_date, end_date = _month_range(today)
        time_label = f"{start_date.strftime('%d/%m/%Y')} - {(end_date - dt.timedelta(days=1)).strftime('%d/%m/%Y')}"

    elif mode == "CUSTOM":
        try:
            if raw_from:
                start_date = dt.datetime.strptime(raw_from, "%Y-%m-%d").date()
            if raw_to:
                to_date = dt.datetime.strptime(raw_to, "%Y-%m-%d").date()
                end_date = to_date + dt.timedelta(days=1)
        except:
            start_date = None
            end_date = None

        if not start_date or not end_date:
            mode = "WEEK"
            start_date = _start_of_week(today)
            end_date = start_date + dt.timedelta(days=7)

        time_label = f"{start_date.strftime('%d/%m/%Y')} - {(end_date - dt.timedelta(days=1)).strftime('%d/%m/%Y')}"

    else:
        mode = "WEEK"
        start_date = _start_of_week(today)
        end_date = start_date + dt.timedelta(days=7)
        time_label = f"{start_date.strftime('%d/%m/%Y')} - {(end_date - dt.timedelta(days=1)).strftime('%d/%m/%Y')}"

    return mode, start_date, end_date, time_label


def get_dashboard_data(mode: str, raw_from: str = "", raw_to: str = ""):
    mode, start_date, end_date, time_label = dashboard_range(mode, raw_from, raw_to)

    start_dt = dt.datetime.combine(start_date, dt.time.min)
    end_dt = dt.datetime.combine(end_date, dt.time.min)

    # ===== KPI =====
    base_hd = (
        db.session.query(HoaDon)
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .filter(HoaDon.ngayThanhToan >= start_dt, HoaDon.ngayThanhToan < end_dt)
    )

    revenue = base_hd.with_entities(func.coalesce(func.sum(HoaDon.tongThanhToan), 0)).scalar() or 0
    orders = base_hd.count()

    items_sold = (
        db.session.query(func.coalesce(func.sum(ChiTietHoaDon.soLuong), 0))
        .join(HoaDon, HoaDon.id == ChiTietHoaDon.hoaDon_id)
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .filter(HoaDon.ngayThanhToan >= start_dt, HoaDon.ngayThanhToan < end_dt)
        .scalar() or 0
    )

    avg_order_value = (revenue / orders) if orders else 0

    kpi = {
        "revenue": float(revenue),
        "revenue_pct": None,
        "orders": int(orders),
        "orders_pct": None,
        "items_sold": int(items_sold),
        "avg_order_value": float(avg_order_value)
    }

    # ===== CHART: doanh thu theo ngày =====
    rows_rev = (
        db.session.query(
            func.date(HoaDon.ngayThanhToan).label("d"),
            func.coalesce(func.sum(HoaDon.tongThanhToan), 0).label("rev")
        )
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .filter(HoaDon.ngayThanhToan >= start_dt, HoaDon.ngayThanhToan < end_dt)
        .group_by(func.date(HoaDon.ngayThanhToan))
        .order_by(func.date(HoaDon.ngayThanhToan))
        .all()
    )
    rev_map = {r.d: float(r.rev) for r in rows_rev}

    labels_day, data_day = [], []
    cur = start_date
    while cur < end_date:
        labels_day.append(cur.strftime("%d/%m"))
        data_day.append(rev_map.get(cur, 0))
        cur += dt.timedelta(days=1)

    # ===== CHART: top danh mục bán chạy (theo số lượng) =====
    nhom_name_map = {
        "CA_PHE": "Cà phê",
        "TRA": "Trà",
        "BANH_NGOT": "Bánh ngọt",
        "KHAC": "Khác"
    }

    cat_rows = (
        db.session.query(
            Mon.nhom.label("nhom"),
            func.coalesce(func.sum(ChiTietHoaDon.soLuong), 0).label("qty")
        )
        .join(ChiTietHoaDon, ChiTietHoaDon.mon_id == Mon.id)
        .join(HoaDon, HoaDon.id == ChiTietHoaDon.hoaDon_id)
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .filter(HoaDon.ngayThanhToan >= start_dt, HoaDon.ngayThanhToan < end_dt)
        .group_by(Mon.nhom)
        .order_by(func.sum(ChiTietHoaDon.soLuong).desc())
        .all()
    )

    top_cat_labels, top_cat_data = [], []
    for nhom, qty in cat_rows:
        key = getattr(nhom, "name", None) or (str(nhom) if nhom else "KHAC")
        top_cat_labels.append(nhom_name_map.get(key, key))
        top_cat_data.append(int(qty or 0))

    charts = {
        "revenue_by_day": {"labels": labels_day, "data": data_day},
        "top_categories": {"labels": top_cat_labels, "data": top_cat_data}
    }

    # ===== TABLE: chi tiết bán hàng theo món =====
    item_rows_q = (
        db.session.query(
            Mon.name.label("name"),
            func.coalesce(func.sum(ChiTietHoaDon.soLuong), 0).label("qty"),
            func.coalesce(func.sum(ChiTietHoaDon.thanhTien), 0).label("revenue")
        )
        .join(ChiTietHoaDon, ChiTietHoaDon.mon_id == Mon.id)
        .join(HoaDon, HoaDon.id == ChiTietHoaDon.hoaDon_id)
        .filter(HoaDon.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN)
        .filter(HoaDon.ngayThanhToan >= start_dt, HoaDon.ngayThanhToan < end_dt)
        .group_by(Mon.id, Mon.name)
        .order_by(func.sum(ChiTietHoaDon.thanhTien).desc())
        .all()
    )
    item_rows = [{"name": r.name, "qty": int(r.qty or 0), "revenue": float(r.revenue or 0)} for r in item_rows_q]

    return mode, time_label, kpi, charts, item_rows


#Kho

def get_inventory_report_data(
    q="",
    group="",
    status="",
    only_low=False,
    include_zero=True,
    sort="name",
    raw_from="",
    raw_to=""
):
    query = NguyenLieu.query

    # ===== SEARCH =====
    if q:
        query = query.filter(NguyenLieu.name.ilike(f"%{q}%"))

    # ===== FILTER: GROUP (Enum name) =====
    if group:
        try:
            query = query.filter(NguyenLieu.nhom == NhomNguyenLieuEnum[group])
        except Exception:
            pass

    # ===== FILTER: INCLUDE ZERO =====
    if not include_zero:
        query = query.filter(NguyenLieu.soLuongTon > 0)

    rows = query.all()

    total_items = len(rows)
    low_count = 0
    out_count = 0
    total_qty = 0

    result_rows = []

    for nl in rows:
        qty = float(nl.soLuongTon or 0)
        min_qty = float(getattr(nl, "soLuongToiThieu", 0) or 0)

        # ===== STATUS (OK/LOW/OUT) =====
        if qty <= 0:
            st = "OUT"
            out_count += 1
        elif qty <= min_qty:
            st = "LOW"
            low_count += 1
        else:
            st = "OK"

        # ===== FILTER: STATUS dropdown (OK/LOW/OUT) =====
        if status and status in ("OK", "LOW", "OUT") and st != status:
            continue

        if only_low and st == "OK":
            continue

        total_qty += qty

        # ===== GROUP LABEL =====
        if getattr(nl, "nhom", None):
            group_key = getattr(nl.nhom, "name", None) or ""
            group_label = getattr(nl.nhom, "value", None) or "Khác"
        else:
            group_key = ""
            group_label = "Khác"

        result_rows.append({
            "id": nl.id,
            "code": nl.id,
            "name": nl.name,

            # dùng cho chart + (nếu bạn muốn) dropdown nhóm
            "group": group_key,
            "group_label": group_label,

            "qty": qty,
            "unit": nl.donViTinh,
            "min_qty": min_qty,
            "suggest_qty": max(0, min_qty - qty),

            "days_cover": None,
            "updated_at": getattr(nl, "ngayTao", None).strftime("%d/%m/%Y")
                          if getattr(nl, "ngayTao", None) else None,
            "location": None,
            "note": None,
            "status": st
        })

    # ===== SORT =====
    if sort == "qty_desc":
        result_rows.sort(key=lambda x: x["qty"], reverse=True)
    elif sort == "qty_asc":
        result_rows.sort(key=lambda x: x["qty"])
    elif sort == "low_first":
        order = {"OUT": 0, "LOW": 1, "OK": 2}
        result_rows.sort(key=lambda x: order.get(x["status"], 3))
    else:
        result_rows.sort(key=lambda x: (x["name"] or "").lower())

    # ===== CHART DATA =====
    by_group = {}
    for r in result_rows:
        g = r.get("group_label") or "Khác"
        by_group[g] = by_group.get(g, 0) + float(r.get("qty") or 0)

    charts = {
        "by_group": {
            "labels": list(by_group.keys()),
            "data": list(by_group.values())
        },
        "by_status": {
            "labels": ["Đủ hàng", "Sắp hết", "Hết hàng"],
            "data": [
                len([r for r in result_rows if r["status"] == "OK"]),
                len([r for r in result_rows if r["status"] == "LOW"]),
                len([r for r in result_rows if r["status"] == "OUT"])
            ]
        }
    }

    group_opts = []
    try:
        for e in NhomNguyenLieuEnum:
            group_opts.append({"value": e.name, "label": e.value})
    except Exception:
        group_opts = []

    return {
        "kpi": {
            "total_items": total_items,
            "low_count": low_count,
            "out_count": out_count,
            "stock_value": 0
        },
        "rows": result_rows,
        "total_qty": total_qty,
        "charts": charts,
        "group_opts": group_opts,
        "time_label": None,
        "export_url": None
    }

