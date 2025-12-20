import os
import os.path as op
from flask import redirect, url_for, render_template_string
# Import các module của Flask-Admin
from flask_admin import Admin, AdminIndexView, expose, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_admin.menu import MenuLink
from flask_admin.form import upload
from flask_login import current_user
from CafeApp import app, db
from CafeApp.dao import get_dashboard_data, get_inventory_report_data
# Import các Models (Bảng dữ liệu) cần quản lý
from CafeApp.models import (
    Mon, NhanVienCuaHang, NguyenLieu, PhieuNhap,
    ChiTietPhieuNhap, CongThuc, BaoCaoDoanhThu
)
from flask import request
# Cấu hình đường dẫn lưu ảnh (Dùng cho phần upload ảnh món ăn)
# Tạo folder 'static/img' nếu chưa tồn tại
path_img = op.join(app.root_path, 'static', 'img')
try:
    os.makedirs(path_img)
except OSError:
    pass


# BASE VIEW - QUẢN LÝ QUYỀN TRUY CẬP CHUNG

# Class cha: Tất cả các trang quản trị đều phải kế thừa class này
# Nhiệm vụ: Kiểm tra xem người dùng đã đăng nhập chưa.
class BaseAdminView(ModelView):
    def is_accessible(self):
        # Trả về True nếu đã đăng nhập, False nếu chưa
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # Nếu chưa đăng nhập (is_accessible trả về False) -> Đá về trang login
        return redirect(url_for('login'))


# PHÂN QUYỀN THEO CHỨC VỤ (ROLE)

# 1. View dành riêng cho KHO (Chỉ Qly Kho mới xem được)
class InventoryView(BaseAdminView):
    def is_accessible(self):
        # Logic: Đã đăng nhập VÀ Chức vụ là Qly Kho
        return current_user.is_authenticated and str(current_user.role.name) == 'QUAN_LY_KHO'


# 2. View dành riêng cho CỬA HÀNG (Chỉ Qly CH mới xem được)
class StoreView(BaseAdminView):
    def is_accessible(self):
        # Logic: Đã đăng nhập VÀ Chức vụ là Qly CH
        return current_user.is_authenticated and str(current_user.role.name) == 'QUAN_LY_CUA_HANG'


# PHẦN 4: CẤU HÌNH CHI TIẾT TỪNG TRANG QUẢN TRỊ

#  A. QUẢN LÝ NHÂN SỰ (Thuộc nhóm StoreView)
class NhanVienView(StoreView):
    column_labels = dict(tenDangNhap='Username', matKhau='Mật khẩu', role='Chức vụ',
                         trangThai='Trạng thái', sdt='SĐT', name='Họ Tên')
    column_list = ('name', 'sdt', 'tenDangNhap', 'role', 'trangThai')
    form_columns = ('name', 'sdt', 'tenDangNhap', 'matKhau', 'role', 'trangThai')
    column_exclude_list = ['matKhau']


# B. QUẢN LÝ NGUYÊN LIỆU (Thuộc nhóm InventoryView)
class NguyenLieuView(InventoryView):
    column_list = ('name', 'donViTinh', 'soLuongTon', 'giaMuaToiThieu', 'trangThai')
    column_labels = dict(name='Tên NL', donViTinh='ĐVT', soLuongTon='Tồn Kho', giaMuaToiThieu='Giá Mua',
                         trangThai='Trạng Thái')

    # Hàm tô màu cảnh báo: Nếu sắp hết hoặc tồn < 10 thì hiện màu đỏ
    def _color_stock(view, context, model, name):
        if str(model.trangThai.name) == 'SAP_HET' or (model.soLuongTon is not None and model.soLuongTon < 10):
            return f'<span style="color: red; font-weight: bold;">{model.soLuongTon} (!!)</span'
        return model.soLuongTon

    # Áp dụng hàm tô màu vào cột 'soLuongTon'
    column_formatters = {'soLuongTon': _color_stock}


#  C. QUẢN LÝ PHIẾU NHẬP (Thuộc nhóm InventoryView)
class PhieuNhapView(InventoryView):
    inline_models = [
        (ChiTietPhieuNhap, dict(form_columns=['id', 'nguyenLieu', 'soLuongNhap', 'donGiaNhap', 'thanhTien']))]
    column_labels = dict(ngayTao='Ngày Tạo', ghiChu='Ghi Chú', tongSoNguyenLieu='Tổng SL', tongGiaTriNhap='Tổng Tiền',
                         nguoiNhap_id='Người Nhập')
    form_columns = ('ngayTao', 'ghiChu', 'nguoiNhap_id')

    # Tự động cộng tồn kho khi tạo phiếu nhập mới
    def on_model_change(self, form, model, is_created):
        if is_created:  # Chỉ chạy khi tạo mới (không chạy khi sửa)
            for chi_tiet in model.chiTiet:
                nl = chi_tiet.nguyenLieu
                if nl:
                    # Cộng dồn số lượng nhập vào kho
                    nl.soLuongTon = (nl.soLuongTon or 0) + chi_tiet.soLuongNhap


#  D. QUẢN LÝ MÓN ĂN (Thuộc nhóm StoreView)
class MonView(StoreView):
    # Cho phép nhập Công Thức (Định lượng) ngay trong form Món
    inline_models = [(CongThuc, dict(form_columns=['id', 'nguyenLieu', 'dinhLuong']))]
    column_labels = dict(name='Tên Món', gia='Giá Bán', trangThai='Trạng Thái', image='Ảnh Minh Họa', moTa='Mô Tả')
    column_list = ('name', 'gia', 'trangThai', 'image')

    # Cấu hình upload ảnh
    form_extra_fields = {
        'image': upload.ImageUploadField('Chọn Ảnh', base_path=path_img, url_relative_path='img/')
    }


# --- E. BÁO CÁO DOANH THU (Chỉ xem, không sửa xóa) ---
class BaoCaoView(StoreView):
    can_create = False  # Tắt nút tạo
    can_delete = False  # Tắt nút xóa
    can_edit = False  # Tắt nút sửa
    column_labels = dict(ngayBaoCao='Ngày', tongDoanhThu='Tổng Doanh Thu', soDonHang='Số Đơn',
                         sanPhamBanChayNhat='SP Bán Chạy')


# DASHBOARD (TRANG CHỦ ADMIN)


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
admin.add_view(NhanVienView(NhanVienCuaHang, db.session, name='Nhân Sự', category='Hệ Thống'))

# Group: Cửa Hàng (Cho Quản lý cửa hàng)
admin.add_view(MonView(Mon, db.session, name='Món Ăn', category='Cửa Hàng'))
admin.add_view(BaoCaoView(BaoCaoDoanhThu, db.session, name='Doanh Thu', category='Cửa Hàng'))

# Group: Kho (Cho Quản lý kho)
admin.add_view(NguyenLieuView(NguyenLieu, db.session, name='Nguyên Liệu', category='Kho'))
admin.add_view(PhieuNhapView(PhieuNhap, db.session, name='Nhập Hàng', category='Kho'))

# Link Đăng xuất
admin.add_link(MenuLink(name='Đăng Xuất', category='', url='/logout'))