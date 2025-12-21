import datetime
import cloudinary
import os
import os.path as op
from flask import redirect, url_for, render_template_string, jsonify
# Import các module của Flask-Admin
from flask_admin import Admin, AdminIndexView, expose, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_admin.menu import MenuLink
from flask_admin.form import upload
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from wtforms import FileField, ValidationError, TimeField

from CafeApp import app, db
from CafeApp.dao import get_dashboard_data, get_inventory_report_data
# Import các Models (Bảng dữ liệu) cần quản lý
from CafeApp.models import (
    Mon, NhanVienCuaHang, NguyenLieu, PhieuNhap,
    ChiTietPhieuNhap, CongThuc, BaoCaoDoanhThu, Topping, MonTopping, NhomNguyenLieuEnum, TrangThaiNguyenLieuEnum,
    NhomMonEnum, ThongBaoKho, SchedulerBot, TrangThaiEnum
)
from flask import request


def format_money(view, context, model, name):
    value = getattr(model, name)
    if value is None:
        return ""
    # Format: 20,000 -> 20.000 VNĐ
    return "{:,.0f} VNĐ".format(value).replace(",", ".")


class BaseAdminView(ModelView):
    page_size = 10
    can_set_page_size = False
    list_template = 'admin/custom_list.html'
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

    #  Trỏ vào file CSS
    extra_css = ['/static/admin_style.css']
    def is_action_allowed(self, name):
        if name == 'delete':
            return False
        return super().is_action_allowed(name)

class InventoryView(BaseAdminView):
    def is_accessible(self):
        return current_user.is_authenticated and str(current_user.role.name) == 'QUAN_LY_KHO'


class StoreView(BaseAdminView):
    def is_accessible(self):
        return current_user.is_authenticated and str(current_user.role.name) == 'QUAN_LY_CUA_HANG'


class NhanVienView(StoreView):
    column_labels = dict(tenDangNhap='Username', matKhau='Mật khẩu', role='Chức vụ', trangThai='Trạng thái', sdt='SĐT',
                         name='Họ Tên')
    column_list = ('name', 'sdt', 'tenDangNhap', 'role', 'trangThai')
    form_columns = ('name', 'sdt', 'tenDangNhap', 'matKhau', 'role', 'trangThai')
    column_exclude_list = ['matKhau']

    def on_model_change(self, form, model, is_created):
        # Nếu có nhập mật khẩu thì băm trước khi lưu
        raw = (model.matKhau or "").strip()
        if raw:
            # Tránh băm lại nếu nó đã là hash
            if not (raw.startswith("pbkdf2:") or raw.startswith("scrypt:")):
                model.matKhau = generate_password_hash(raw)

        return super().on_model_change(form, model, is_created)

class NguyenLieuView(InventoryView):
    can_delete = False
    column_list = ('name', 'donViTinh', 'nhom', 'soLuongTon', 'soLuongToiThieu', 'giaMuaToiThieu', 'trangThai')

    column_labels = dict(
        name='Tên Nguyên Liệu',
        donViTinh='ĐVT',
        soLuongTon='Tồn Kho',
        giaMuaToiThieu='Giá Mua',
        trangThai='Trạng Thái',
        soLuongToiThieu='Mức Tối Thiểu',
        nhom='Nhóm'
    )
    form_columns = ('name', 'donViTinh', 'nhom', 'giaMuaToiThieu', 'soLuongTon', 'soLuongToiThieu', 'trangThai')

    def on_model_change(self, form, model, is_created):
        # 1) Logic khởi tạo (Chỉ chạy khi tạo mới)
        if is_created:
            if model.soLuongTon is None:
                model.soLuongTon = 0
            if model.soLuongToiThieu is None:
                model.soLuongToiThieu = 5
            if model.nhom is None:
                model.nhom = NhomNguyenLieuEnum.KHAC

        # 2) Nếu admin chọn "Ngưng sử dụng" -> giữ nguyên (không auto-đè)
        if model.trangThai == TrangThaiNguyenLieuEnum.NGUNG_SU_DUNG:
            return super().on_model_change(form, model, is_created)

        # 3) Auto tính trạng thái theo tồn kho / tối thiểu
        qty = float(model.soLuongTon or 0)
        min_qty = float(model.soLuongToiThieu or 0)

        if qty <= 0:
            model.trangThai = TrangThaiNguyenLieuEnum.HET_HANG
        elif qty <= min_qty:
            model.trangThai = TrangThaiNguyenLieuEnum.SAP_HET
        else:
            model.trangThai = TrangThaiNguyenLieuEnum.CON_HANG

        return super().on_model_change(form, model, is_created)

    # 3. Cập nhật màu sắc hiển thị cho đẹp
    def _color_stock(view, context, model, name):
        # Nếu ngừng sử dụng thì hiện màu xám, gạch ngang
        if str(model.trangThai.name) == 'NGUNG_SU_DUNG':
            return Markup(
                f'<span style="color: #999; text-decoration: line-through;">{model.soLuongTon} (Đã ngưng)</span>')
        # Nếu sắp hết hàng thì tô màu đỏ
        limit = model.soLuongToiThieu
        if str(model.trangThai.name) == 'SAP_HET' or (model.soLuongTon is not None and model.soLuongTon <= limit):
            return Markup(f'<span style="color: red; font-weight: bold;">{model.soLuongTon} (!!!)</span>')
        return model.soLuongTon

    #  Format tiền tệ
    column_formatters = {
        'soLuongTon': _color_stock,
        'giaMuaToiThieu': format_money
    }

#  C. QUẢN LÝ PHIẾU NHẬP (Thuộc nhóm InventoryView)
class PhieuNhapView(InventoryView):
    # Tắt Sửa/Xóa, Bật Xem chi tiết
    can_delete = False
    can_edit = False
    can_view_details = True

    # ===== Labels =====
    column_labels = dict(
        name='Mã Phiếu',
        ngayTao='Ngày Tạo',
        nguoiNhap='Người Nhập',
        ghiChu='Ghi Chú',
        tongSoNguyenLieu='Tổng SL',
        tongGiaTriNhap='Tổng Tiền',
        chiTiet='Chi Tiết Nhập'
    )

    # ===== LIST (bảng danh sách) =====
    # Không show chiTiet ở list để khỏi dài — bấm con mắt để xem
    column_list = ('name', 'ngayTao', 'nguoiNhap', 'ghiChu', 'tongSoNguyenLieu', 'tongGiaTriNhap')

    # ===== DETAILS (bấm con mắt) =====
    # Cho hiện chiTiet ở Details
    column_details_list = (
        'name', 'ngayTao', 'nguoiNhap', 'ghiChu',
        'tongSoNguyenLieu', 'tongGiaTriNhap',
        'chiTiet'
    )

    # ===== CREATE FORM =====
    form_columns = ('ngayTao', 'ghiChu')

    # Cho phép nhập danh sách nguyên liệu (inline)
    inline_models = [
        (ChiTietPhieuNhap, dict(
            form_columns=['id', 'nguyenLieu', 'soLuongNhap', 'donGiaNhap'],
            form_label='Chi Tiết Nhập Hàng',
            column_labels={
                'nguyenLieu': 'Nguyên Liệu',
                'soLuongNhap': 'Số Lượng Nhập',
                'donGiaNhap': 'Đơn Giá Nhập'
            },
            form_args={
                'nguyenLieu': {
                    'query_factory': NguyenLieu.get_active_ingredients_list
                }
            }
        ))
    ]

    # ===== FORMATTERS =====
    def _fmt_nguoi_nhap(view, context, model, name):
        # model.nguoiNhap là relationship
        if getattr(model, "nguoiNhap", None):
            return model.nguoiNhap.tenDangNhap or model.nguoiNhap.name or ""
        return ""

    def _fmt_chi_tiet_detail(view, context, model, name):
        rows = getattr(model, "chiTiet", None) or []
        if not rows:
            return Markup("<em>Không có chi tiết.</em>")

        html = """
        <table class="table table-sm table-bordered" style="max-width:900px;margin-bottom:0;">
          <thead>
            <tr>
              <th>Tên nguyên liệu</th>
              <th style="width:120px">SL nhập</th>
              <th style="width:140px">Đơn giá</th>
              <th style="width:160px">Thành tiền</th>
            </tr>
          </thead>
          <tbody>
        """

        for ct in rows:
            ten = getattr(getattr(ct, "nguyenLieu", None), "name", "") or ""
            sl = ct.soLuongNhap or 0
            dg = ct.donGiaNhap or 0
            tt = ct.thanhTien if getattr(ct, "thanhTien", None) is not None else (float(sl) * float(dg))

            dg_fmt = "{:,.0f} VNĐ".format(dg).replace(",", ".")
            tt_fmt = "{:,.0f} VNĐ".format(tt).replace(",", ".")

            html += f"""
              <tr>
                <td>{ten}</td>
                <td>{sl}</td>
                <td>{dg_fmt}</td>
                <td><b>{tt_fmt}</b></td>
              </tr>
            """

        html += "</tbody></table>"
        return Markup(html)

    # formatter cho LIST + DETAILS (các field thường)
    column_formatters = {
        'tongGiaTriNhap': format_money,
        'nguoiNhap': _fmt_nguoi_nhap,
    }

    # formatter CHỈ cho DETAILS (bấm con mắt) để hiện bảng chi tiết
    column_formatters_detail = {
        'tongGiaTriNhap': format_money,
        'nguoiNhap': _fmt_nguoi_nhap,
        'chiTiet': _fmt_chi_tiet_detail,
    }

    # ===== SAVE LOGIC =====
    def on_model_change(self, form, model, is_created):
        # 1) Tự động điền thông tin phiếu (Người nhập, Mã phiếu)
        if is_created:
            model.nguoiNhap_id = current_user.id
            model.name = "PN" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        tong_sl = 0.0
        tong_tien = 0.0

        # 2) Duyệt từng chi tiết để tính toán + cập nhật kho
        for chi_tiet in (model.chiTiet or []):
            sl_nhap = float(chi_tiet.soLuongNhap) if chi_tiet.soLuongNhap else 0.0
            don_gia = float(chi_tiet.donGiaNhap) if chi_tiet.donGiaNhap else 0.0

            thanh_tien_dong = sl_nhap * don_gia
            chi_tiet.thanhTien = thanh_tien_dong

            nl = getattr(chi_tiet, "nguyenLieu", None)
            if nl:
                ton_kho_cu = float(nl.soLuongTon) if nl.soLuongTon else 0.0
                nl.soLuongTon = ton_kho_cu + sl_nhap

            tong_sl += sl_nhap
            tong_tien += thanh_tien_dong

        # 3) Lưu tổng
        model.tongSoNguyenLieu = tong_sl
        model.tongGiaTriNhap = tong_tien

        return super().on_model_change(form, model, is_created)


class MonView(StoreView):
    can_delete = False
    column_list = ('name', 'nhom', 'gia', 'id', 'trangThai', 'image')
    column_labels = dict(
        name='Tên Món',
        nhom='Nhóm',
        gia='Giá Bán',
        id='Topping Kèm',
        trangThai='Trạng Thái',
        image='Ảnh Minh Họa',
        moTa='Mô Tả'
    )

    inline_models = [
        # 1. Bảng Công thức
        (CongThuc, dict(
            form_columns=['id', 'nguyenLieu', 'dinhLuong'],
            form_label='Công Thức Pha Chế',
            column_labels={'nguyenLieu': 'Nguyên Liệu', 'dinhLuong': 'Định Lượng'},
            form_args={
                'nguyenLieu': {
                    'query_factory': NguyenLieu.get_active_ingredients_list
                }
            }
        )),

        # 2. Bảng Topping đi kèm
        (MonTopping, dict(
            form_columns=['id', 'topping', 'override_price', 'is_allowed'],
            form_label='Topping Đi Kèm',
            column_labels={
                'topping': 'Loại Topping',
                'override_price': 'Giá Riêng',
                'is_allowed': 'Cho Phép'
            },
            form_args={
                'topping': {
                    'query_factory': Topping.get_active_toppings_list
                }
            }
        ))
    ]

    # Trick lỏ để cho labels Topping đi kèm format đồng bộ với những labels kia
    form_columns = ('name', 'nhom', 'gia', 'moTa', 'trangThai', 'image')
    column_sortable_list = (
        'name',
        'nhom',
        'gia',
        'trangThai',
        'id',
        'image'
    )
    form_overrides = {
        'image': FileField
    }

    def on_model_change(self, form, model, is_created):
        # Kiểm tra xem người dùng có chọn file ảnh mới không
        file_data = form.image.data
        # Nếu có file và file đó hợp lệ
        if file_data and hasattr(file_data, 'read'):
            try:
                # 1. Upload lên Cloudinary
                res = cloudinary.uploader.upload(file_data)
                # 2. Lấy đường link HTTPS
                url_anh = res['secure_url']
                # 3. Gán link vào database
                model.image = url_anh
            except Exception as e:
                print(f"Lỗi upload ảnh: {e}")

        if is_created:
            if not model.nhom:
                model.nhom = NhomMonEnum.KHAC

        return super().on_model_change(form, model, is_created)

    # Hàm hiển thị Thumbnail
    def _list_thumbnail(view, context, model, name):
        if not model.image:
            return ''
        # Hiển thị ảnh từ link Cloudinary
        return Markup(
            f'<img src="{model.image}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;">')

    # Hàm định dạng hiển thị Topping
    def _list_toppings(_view, _context, model, _name):
        names = [
            item.topping.name
            for item in model.topping_links
            # Điều kiện: Phải có topping VÀ topping đó đang bật (is_active=True)
            if item.topping and item.topping.is_active
        ]
        return ", ".join(names)

    column_formatters = {
        'gia': format_money,
        'id': _list_toppings,
        'image': _list_thumbnail
    }


class ToppingView(StoreView):
    can_delete = False
    column_list = ('name', 'code', 'price', 'is_active')
    column_labels = dict(name='Tên Topping', code='Mã (id)', price='Giá Bán Thêm', is_active='Đang Dùng')
    form_columns = ('name', 'code', 'price', 'is_active')

    column_formatters = {
        'price': format_money
    }

#  D. QUẢN LÝ MÓN ĂN (Thuộc nhóm StoreView)


# --- E. BÁO CÁO DOANH THU (Chỉ xem, không sửa xóa) ---
class BaoCaoView(StoreView):
    can_create = False  # Tắt nút tạo
    can_delete = False  # Tắt nút xóa
    can_edit = False  # Tắt nút sửa
    column_labels = dict(ngayBaoCao='Ngày', tongDoanhThu='Tổng Doanh Thu', soDonHang='Số Đơn',
                         sanPhamBanChayNhat='SP Bán Chạy')


class CongThucView(StoreView):
    # Chỉ cho xem và sửa, không cho xóa Món ở đây (tránh xóa nhầm mất món)
    can_delete = False
    can_create = False
    can_edit = True
    list_template = 'admin/model/list.html'
    #   CẤU HÌNH XUẤT FILE (EXCEL/CSV)
    can_export = True
    export_types = ['csv']  # Xuất ra file CSV (Excel đọc được)
    export_columns = ['name', 'moTa']

    column_list = ('name', 'chi_tiet_cong_thuc')
    column_labels = dict(name='Tên Món', chi_tiet_cong_thuc='Công Thức Chi Tiết')

    # Ô tìm kiếm để lọc món nhanh
    column_searchable_list = ['name']

    #   CẤU HÌNH FORM SỬA (CHỈ HIỆN CÔNG THỨC)
    form_columns = ('name', 'congThuc')

    # Ẩn tên món đi để chỉ đọc (không cho sửa tên món ở đây)
    form_widget_args = {
        'name': {
            'disabled': True
        }
    }

    #   INLINE MODEL: ĐỂ SỬA CÔNG THỨC TRỰC TIẾP
    inline_models = [
        (CongThuc, dict(
            form_columns=['id', 'nguyenLieu', 'dinhLuong'],
            form_label='Thành Phần',
            column_labels={'nguyenLieu': 'Nguyên Liệu', 'dinhLuong': 'Định Lượng'},

            # Vẫn giữ logic lọc nguyên liệu đang còn
            form_args={
                'nguyenLieu': {
                    'query_factory': NguyenLieu.get_active_ingredients_list
                }
            }
        ))
    ]

    def _format_cong_thuc(view, context, model, name):
        # 1. Bắt lỗi (Try-Except) để nếu code sai thì nó hiện thông báo lỗi lên màn hình
        try:
            if not model.congThuc:
                return Markup('<em>Chưa có công thức</em>')
            html = '<ul style="padding-left: 20px; margin: 0;">'
            for ct in model.congThuc:
                nl = ct.nguyenLieu
                if nl:
                    # Lấy tên trạng thái an toàn (tránh lỗi nếu trangThai bị None)
                    trang_thai_name = str(nl.trangThai.name) if nl.trangThai else ""
                    if trang_thai_name == 'NGUNG_SU_DUNG':
                        # Hiện cảnh báo đỏ
                        nl_name_display = f'<span style="color: red;">⚠️ {nl.name} (Đã ngưng)</span>'
                    else:
                        nl_name_display = nl.name
                    html += f'<li><b>{nl_name_display}:</b> {ct.dinhLuong} {nl.donViTinh}</li>'
                else:
                    # Trường hợp không tìm thấy nguyên liệu (đã bị xóa vĩnh viễn khỏi DB)
                    html += f'<li><b>(Dữ liệu lỗi - Mất NL):</b> {ct.dinhLuong}</li>'

            html += '</ul>'
            return Markup(html)

        except Exception as e:
            # Nếu có lỗi gì, in lỗi đó ra màn hình để biết nguyên nhân
            print(f"LỖI FORMAT: {e}")
            return Markup(f'<span style="color:red">Lỗi code: {str(e)}</span>')

    column_formatters = {
        'chi_tiet_cong_thuc': _format_cong_thuc
    }

class ThongBaoKhoView(InventoryView):
    can_create = False
    can_edit = True   # để mark read
    can_delete = False

    form_columns = ("trang_thai",)

    column_list = ("created_at", "loai", "trang_thai", "message", "nguyenLieu")
    column_labels = dict(
        created_at="Thời gian",
        loai="Loại",
        trang_thai="Trạng thái",
        message="Nội dung",
        nguyenLieu="Nguyên liệu"
    )

    def get_query(self):
        q = super().get_query()
        return q.order_by(ThongBaoKho.created_at.desc())

class CauHinhBaoTonView(InventoryView):
    can_create = True
    can_edit = True
    can_delete = True

    list_template = "admin/bao_ton_list.html"
    create_template = "admin/bao_ton_create.html"

    column_display_actions = False


    form_overrides = {
        "gioChayHangNgay": TimeField
    }
    form_args = {
        "gioChayHangNgay": {
            "format": "%H:%M"
        }
    }

    # ===== LIST =====
    column_list = ("edit_col", "delete_col", "gioChayHangNgay", "toggle_col", "last_run_date")

    column_labels = dict(
        edit_col="Sửa",
        delete_col="Xóa",
        gioChayHangNgay="Thời gian",
        toggle_col="Trạng thái",
        last_run_date="Lần chạy gần nhất"
    )

    # ===== FORM (Create/Edit) =====
    form_columns = ("gioChayHangNgay", "trangThai")

    # ====== formatter cho 2 cột Sửa/Xóa ======
    def _fmt_edit(view, context, model, name):
        url = view.get_url(".edit_view", id=model.id, url=request.url)
        return Markup(f"""
            <a class="btn btn-link p-0" href="{url}" title="Sửa">
                <i class="fa fa-pencil"></i>
            </a>
        """)

    def _fmt_delete(view, context, model, name):
        post_url = view.get_url(".delete_view")  # endpoint delete_view
        return Markup(f"""
          <form method="post" action="{post_url}" style="display:inline;"
                onsubmit="return confirm('Xóa bot này?');">
            <input type="hidden" name="id" value="{model.id}">
            <button type="submit" class="btn btn-link p-0 text-danger" title="Xóa">
              <i class="fa fa-trash"></i>
            </button>
          </form>
        """)

    # ====== Toggle iOS ======
    def _fmt_toggle(view, context, model, name):
        is_active = getattr(model.trangThai, "name", str(model.trangThai)) == "ACTIVE"
        checked = "checked" if is_active else ""
        url = view.get_url(".toggle_bot", id=model.id)

        return Markup(f"""
        <label class="ios-switch">
          <input type="checkbox" {checked}
                 onchange="toggleBot('{url}', this)">
          <span class="ios-slider"></span>
        </label>
        """)

    column_formatters = {
        "edit_col": _fmt_edit,
        "delete_col": _fmt_delete,
        "toggle_col": _fmt_toggle,
    }

    def validate_gioChayHangNgay(self, form, field):
        if not field.data:
            raise ValidationError("Vui lòng chọn thời gian.")

        hhmm = field.data.strftime("%H:%M")  # field.data chắc chắn là datetime.time

        q = SchedulerBot.query.filter(
            func.date_format(SchedulerBot.gioChayHangNgay, "%H:%i") == hhmm
        )

        # khi edit thì loại trừ chính nó
        if getattr(form, "_obj", None) and getattr(form._obj, "id", None):
            q = q.filter(SchedulerBot.id != form._obj.id)

        if q.first():
            raise ValidationError(f"Giờ chạy {hhmm} đã tồn tại. Vui lòng chọn giờ khác.")

    # ===== Toggle API =====
    @expose("/toggle/<int:id>", methods=["POST"])
    def toggle_bot(self, id):
        bot = SchedulerBot.query.get_or_404(id)

        if getattr(bot.trangThai, "name", str(bot.trangThai)) == "ACTIVE":
            bot.trangThai = TrangThaiEnum.INACTIVE
        else:
            bot.trangThai = TrangThaiEnum.ACTIVE

        db.session.commit()
        return jsonify({"ok": True, "status": getattr(bot.trangThai, "name", str(bot.trangThai))})


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # 1) Kiểm tra đăng nhập
        if not current_user.is_authenticated:
            return redirect(url_for('login_my_user'))  # đổi đúng endpoint login của bạn

        role = getattr(current_user.role, "name", None) or str(current_user.role)

        if role == 'QUAN_LY_KHO':
            data = get_inventory_report_data(
                q=(request.args.get('q', '') or '').strip(),
                status=(request.args.get('status', '') or '').strip(),
                only_low=(request.args.get('only_low') == '1'),
                include_zero=(request.args.get('include_zero', '1') == '1'),
                sort=(request.args.get('sort', 'name') or 'name').strip(),
                group=(request.args.get('group', '') or '').strip(),
                raw_from=(request.args.get('from', '') or '').strip(),
                raw_to=(request.args.get('to', '') or '').strip(),
            )
            return self.render('admin/inventory_report.html', **data)

        if role == 'QUAN_LY_CUA_HANG':
            mode = (request.args.get("mode") or "WEEK").upper()
            raw_from = (request.args.get("from") or "").strip()
            raw_to = (request.args.get("to") or "").strip()

            mode, time_label, kpi, charts, item_rows = get_dashboard_data(mode, raw_from, raw_to)

            return self.render(
                "admin/dashboard_chart.html",
                mode=mode,
                time_label=time_label,
                kpi=kpi,
                charts=charts,
                item_rows=item_rows
            )

        return redirect(url_for('index'))


# PHẦN 6: KHỞI TẠO VÀ ĐĂNG KÝ


# Khởi tạo đối tượng Admin
admin = Admin(app,
              name='Cafe Manager',
              theme=Bootstrap4Theme(swatch='flatly'),  # Giao diện Flatly
              index_view=MyAdminIndexView()  # Dùng Dashboard tự tạo ở trên
              )

# Đăng ký các View vào hệ thống menu
# Group: Hệ Thống
# Đăng ký View
admin.add_view(CauHinhBaoTonView(
    SchedulerBot, db.session,
    name="Cấu Hình Báo Tồn",
    category="Kho",
    endpoint="bao_ton"
))
admin.add_view(ThongBaoKhoView(ThongBaoKho, db.session, name="Thông Báo Kho", category="Kho"))
admin.add_view(PhieuNhapView(PhieuNhap, db.session,
                            name='Nhập Hàng', category='Kho',
                            endpoint="phieu_nhap"))
admin.add_view(NhanVienView(NhanVienCuaHang, db.session, name='Nhân Sự', category='Hệ Thống'))
admin.add_view(MonView(Mon, db.session, name='Món', category='Cửa Hàng'))
# admin.add_view(BaoCaoView(BaoCaoDoanhThu, db.session, name='Doanh Thu', category='Cửa Hàng'))
admin.add_view(NguyenLieuView(NguyenLieu, db.session, name='Nguyên Liệu', category='Kho'))
admin.add_view(ToppingView(Topping, db.session, name='Topping', category='Cửa Hàng'))
admin.add_view(CongThucView(Mon, db.session, name='Quản Lý Công Thức', endpoint='quan-ly-cong-thuc', category='Cửa Hàng'))
# Link Đăng xuất
# admin.add_link(MenuLink(name='Đăng Xuất', category='', url='/logout'))