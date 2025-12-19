
import hashlib
from datetime import datetime

from dataclasses import dataclass
from typing import List, Tuple
from CafeApp import db, app
from flask import session
from CafeApp.models import NhanVienCuaHang, SizeEnum, Topping, MonTopping, TrangThaiHoaDonEnum, ChiTietHoaDon, \
    LoaiDungEnum, HoaDon, ChiTietHoaDonTopping, KhachHang


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
        size = _coerce_size(opt.get("size"))
        muc_duong = int(opt.get("duong", opt.get("mucDuong", 100)) or 100)
        muc_da = int(opt.get("da", opt.get("mucDa", 100)) or 100)
        topping_raw = opt.get("topping") or []
        note = (opt.get("note") or "").strip()

        total_qty += qty
        subtotal += price * qty

        items.append({
            "key": key,
            "mon_id": it.get("id"),
            "name": it.get("name", ""),
            "qty": qty,
            "unit_price": price,         # giá 1 ly (đã gồm topping nếu bạn tính vậy)
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
    loai_str = session.get("pos_order_type", "TAI_QUAN")  # "TAI_QUAN"/"MANG_DI"/"TAI_NHA"
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

        db.session.commit()

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