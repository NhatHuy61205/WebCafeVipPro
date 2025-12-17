from flask import Flask, redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_admin.theme import Bootstrap4Theme
from flask_admin.menu import MenuLink
from app import app, db
from app.models import (
    NhanVienCuaHang, NguyenLieu, PhieuNhap, ChiTietPhieuNhap,
    Mon, CongThuc, BaoCaoDoanhThu, RoleEnum, TrangThaiNguyenLieuEnum
)

#  CẤU HÌNH FLASK-LOGIN ---
app.secret_key = 'super_secret_key_admin'

login_manager = LoginManager()
login_manager.init_app(app)

# Đặt tên view login là 'admin_login' để không trùng với user thường
login_manager.login_view = 'admin_login'


# Cấu hình để NhanVienCuaHang hoạt động như User
def config_user_model():
    if not hasattr(NhanVienCuaHang, 'is_authenticated'):
        NhanVienCuaHang.is_authenticated = True
        NhanVienCuaHang.is_active = True
        NhanVienCuaHang.is_anonymous = False
        NhanVienCuaHang.get_id = lambda self: str(self.id)


config_user_model()


@login_manager.user_loader
def load_user(user_id):
    return NhanVienCuaHang.query.get(int(user_id))


# --- PHÂN QUYỀN (PERMISSION) ---

class BaseAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # Redirect về trang đăng nhập admin
        return redirect(url_for('admin_login'))


class InventoryView(BaseAdminView):
    def is_accessible(self):
        # Cho phép QUAN_LY_KHO hoặc NHAN_VIEN để test
        return current_user.is_authenticated and current_user.role in [RoleEnum.QUAN_LY_KHO, RoleEnum.NHAN_VIEN]


class StoreView(BaseAdminView):
    def is_accessible(self):
        # Cho phép QUAN_LY_CUA_HANG hoặc NHAN_VIEN
        return current_user.is_authenticated and current_user.role in [RoleEnum.QUAN_LY_CUA_HANG, RoleEnum.NHAN_VIEN]


# --- GIAO DIỆN CHI TIẾT ---

class NguyenLieuView(InventoryView):
    column_list = ('name', 'donViTinh', 'soLuongTon', 'giaMuaToiThieu', 'trangThai')
    column_labels = dict(name='Tên Nguyên Liệu', donViTinh='Đơn Vị', soLuongTon='Tồn Kho', giaMuaToiThieu='Giá Mua',
                         trangThai='Trạng Thái')

    # Tô màu đỏ cảnh báo nếu sắp hết hàng
    def _color_stock(view, context, model, name):
        if model.trangThai == TrangThaiNguyenLieuEnum.SAP_HET or model.soLuongTon < 10:
            return f'<span style="color: red; font-weight: bold;">{model.soLuongTon} (!!)</span'
        return model.soLuongTon

    column_formatters = {'soLuongTon': _color_stock}


class PhieuNhapView(InventoryView):
    # Nhập chi tiết phiếu ngay trong form tạo phiếu
    inline_models = [
        (ChiTietPhieuNhap, dict(form_columns=['id', 'nguyenLieu', 'soLuongNhap', 'donGiaNhap', 'thanhTien']))]
    column_labels = dict(ngayTao='Ngày Tạo', ghiChu='Ghi Chú', tongSoNguyenLieu='Tổng SL', tongGiaTriNhap='Tổng Tiền',
                         nguoiNhap_id='Người Nhập')
    form_columns = ('ngayTao', 'ghiChu', 'nguoiNhap_id')


class MonView(StoreView):
    # Sửa công thức ngay trong form sửa món
    inline_models = [(CongThuc, dict(form_columns=['id', 'nguyenLieu', 'dinhLuong']))]
    column_labels = dict(name='Tên Món', gia='Giá Bán', trangThai='Trạng Thái', image='Ảnh', moTa='Mô Tả')
    column_list = ('name', 'gia', 'trangThai')


class BaoCaoView(StoreView):
    can_create = False
    can_delete = False
    can_edit = False


# ---  KHỞI TẠO ADMIN ---

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return super(MyAdminIndexView, self).index()


# Khởi tạo Admin với Theme Bootstrap 4
admin = Admin(
    app,
    name='Cafe Manager',
    theme=Bootstrap4Theme(swatch='lux'),
    index_view=MyAdminIndexView()
)
admin.add_link(MenuLink(name='Đăng Xuất', category='', url='/logout'))
admin.add_view(NguyenLieuView(NguyenLieu, db.session, name='Nguyên Liệu', category='Kho'))
admin.add_view(PhieuNhapView(PhieuNhap, db.session, name='Nhập Hàng', category='Kho'))
admin.add_view(MonView(Mon, db.session, name='Món Ăn', category='Cửa Hàng'))
admin.add_view(BaoCaoView(BaoCaoDoanhThu, db.session, name='Doanh Thu', category='Cửa Hàng'))


# --- ROUTES ĐĂNG NHẬP RIÊNG CHO ADMIN ---
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Lưu ý: Đang so sánh plain text để test. Mốt nhớ sửa thành dạng hash.
        user = NhanVienCuaHang.query.filter_by(tenDangNhap=username).first()
        if user and user.matKhau == password:
            login_user(user)
            return redirect('/admin')
        else:
            return "<h1>Sai tài khoản hoặc mật khẩu! <a href='/admin-login'>Thử lại</a></h1>"

    return '''
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
    <div class="container" style="margin-top: 100px; max-width: 400px;">
        <div class="card">
            <div class="card-header bg-dark text-white text-center">
                <h4>Đăng Nhập Quản Trị</h4>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label>Tên đăng nhập</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Mật khẩu</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-dark btn-block">Đăng Nhập</button>
                </form>
            </div>
        </div>
    </div>
    '''


@app.route('/admin-logout')
def admin_logout():
    logout_user()
    return redirect('/admin-login')


if __name__ == '__main__':
    print("Truy cập trang quản trị tại: http://127.0.0.1:5001/admin")
    app.run(debug=True, port=5001)