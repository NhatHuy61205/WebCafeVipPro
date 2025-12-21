from sqlalchemy import Column, Integer, Time, String, DateTime, Enum as SqlEnum, Date, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from CafeApp import db, app
import datetime
from enum import Enum


class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, nullable= True, unique=True)
    name = Column(String(150), nullable=False)
    ngayTao = Column(DateTime, default=datetime.datetime.now)

    def __str__(self):
        return self.name


class RoleEnum(Enum):
    NHAN_VIEN = "NHAN_VIEN"
    QUAN_LY_KHO = "QUAN_LY_KHO"
    QUAN_LY_CUA_HANG = "QUAN_LY_CUA_HANG"


class TrangThaiEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class NhanVienCuaHang(Base, UserMixin):

    sdt = Column(String(20), nullable=False, unique=True)
    tenDangNhap = Column(String(100), nullable=True, unique=True)
    matKhau = Column(String(300), nullable=True)
    role = Column( SqlEnum(RoleEnum), nullable=False, default=RoleEnum.NHAN_VIEN)
    trangThai = Column( SqlEnum(TrangThaiEnum),default=TrangThaiEnum.ACTIVE)


class LoaiDungEnum(Enum):
    TAI_QUAN = "TAI_QUAN"
    TAI_NHA = "TAI_NHA"
    MANG_DI = "MANG_DI"


class KhachHang(Base):

    sdt = Column(String(20), nullable=False, unique=True)
    diaChi = Column(String(255), nullable=True)
    tongDonHangDaMua = Column(Integer, default=0)
    loaiKhachHang = Column(SqlEnum(LoaiDungEnum),nullable=False)
    email = Column(String(150), nullable=True, unique=True)
    hoaDons = relationship("HoaDon", back_populates="khachHang")

class TrangThaiHoaDonEnum(Enum):
    HUY = "HUY"
    CHO_THANH_TOAN = "CHO_THANH_TOAN"
    DA_THANH_TOAN = "DA_THANH_TOAN"



class HoaDon(Base):

    ngayThanhToan = Column(DateTime, nullable=True,default=datetime.datetime.now())
    soBan = Column(Integer, nullable=True)
    tongTienHang = Column(Float, default=0.0)
    thue = Column(Float, default=0.0)
    phiPhucVu = Column(Float, default=0.0)
    giamGia = Column(Float, default=0.0)
    tongThanhToan = Column(Float, default=0.0)
    loaiHoaDon = Column(SqlEnum(LoaiDungEnum),nullable=False)
    trangThai = Column(SqlEnum(TrangThaiHoaDonEnum),default=TrangThaiHoaDonEnum.CHO_THANH_TOAN)
    khachHang_id = Column(Integer, ForeignKey(KhachHang.__table__.c.id), nullable=True)
    maThamChieu = Column(String(50), unique=True, nullable=True)
    ngayTao = Column(DateTime, default=datetime.datetime.now())
    khachHang = relationship("KhachHang", back_populates="hoaDons")


class TrangThaiMonEnum(Enum):
    DANG_BAN = "DANG_BAN"
    TAM_HET = "TAM_HET"
    NGUNG_BAN = "NGUNG_BAN"

class LoaiMonEnum(Enum):
    NUOC = "NUOC"
    BANH = "BANH"

class NhomMonEnum(Enum):
    CA_PHE = "CA_PHE"
    TRA = "TRA"
    BANH_NGOT = "BANH_NGOT"
    KHAC = "KHAC"

class Mon(Base):
    chiTietHoaDon = relationship("ChiTietHoaDon", back_populates="mon", lazy=True)
    congThuc = relationship("CongThuc", backref="mon", lazy=True, cascade="all, delete-orphan")
    topping_links = db.relationship("MonTopping", back_populates="mon")

    gia = Column(Float, nullable=False)
    moTa = Column(String(255), nullable=True)
    trangThai = Column(SqlEnum(TrangThaiMonEnum), default=TrangThaiMonEnum.DANG_BAN)
    image = Column(String(255), nullable = True)
    loaiMon = Column(SqlEnum(LoaiMonEnum), nullable=False, default=LoaiMonEnum.NUOC)
    nhom = db.Column( SqlEnum(NhomMonEnum, native_enum=False),nullable=True)

    @property
    def allowed_toppings(self):
        return [link for link in self.topping_links if link.is_allowed and link.topping and link.topping.is_active]

class SizeEnum(Enum):
    S = "S"
    M = "M"
    L ="L"

class ChiTietHoaDon(db.Model):

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=True)
    soLuong = Column(Integer, nullable=False)
    donGia = Column(Float, nullable=False)
    thanhTien = Column(Float, nullable=False)
    ghiChu = Column(String(255), nullable=True)

    size = Column(SqlEnum(SizeEnum), default=SizeEnum.S)
    mucDuong = Column(Integer, nullable=False, default=100)  # 0/30/50/70/100...
    mucDa = Column(Integer, nullable=False, default=100)

    hoaDon_id = Column(Integer, ForeignKey(HoaDon.__table__.c.id), nullable=False)
    mon_id = Column(Integer, ForeignKey(Mon.__table__.c.id), nullable=False)

    hoaDon = relationship("HoaDon", backref="chiTiet")
    mon = relationship("Mon", back_populates="chiTietHoaDon")
    topping_links = db.relationship(
        "ChiTietHoaDonTopping",
        back_populates="chi_tiet",
        cascade="all, delete-orphan"
    )

class TrangThaiThanhToanEnum(Enum):
    CHO_XU_LY = "CHO_XU_LY"
    THANH_CONG = "THANH_CONG"
    THAT_BAI = "THAT_BAI"



class Topping(Base):
    code = db.Column(db.String(50), unique=True, nullable=False)   # TRAN_CHAU            # Trân châu
    price = db.Column(db.Integer, nullable=False, default=0)      # giá mặc định
    is_active = db.Column(db.Boolean, default=True)
    mon_toppings = db.relationship("MonTopping", back_populates="topping", cascade="all, delete-orphan")
    @staticmethod
    def get_active_toppings_list():
        return Topping.query.filter(Topping.is_active == True).all()


class MonTopping(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    mon_id = db.Column(db.Integer, db.ForeignKey(Mon.__table__.c.id), nullable=False)
    topping_id = db.Column(db.Integer, db.ForeignKey(Topping.__table__.c.id), nullable=False)


    override_price = db.Column(db.Integer, nullable=True)
    is_allowed = db.Column(db.Boolean, default=True)

    mon = db.relationship("Mon", back_populates="topping_links")
    topping = db.relationship("Topping", back_populates="mon_toppings")

    __table_args__ = (
        db.UniqueConstraint('mon_id', 'topping_id', name='unique_mon_topping'),
    )


class ChiTietHoaDonTopping(db.Model):

    chi_tiet_hoa_don_id = db.Column(db.Integer, db.ForeignKey(ChiTietHoaDon.__table__.c.id), primary_key=True)
    topping_id = db.Column(db.Integer, db.ForeignKey(Topping.__table__.c.id), primary_key=True)

    qty = db.Column(db.Integer, default=1)
    price_at_time = db.Column(db.Integer, nullable=False, default=0)

    chi_tiet = db.relationship("ChiTietHoaDon", back_populates="topping_links")
    topping = db.relationship("Topping")



class ThanhToan(Base):

    soTien = Column(Float, nullable=False)
    trangThai = Column(SqlEnum(TrangThaiThanhToanEnum), default=TrangThaiThanhToanEnum.CHO_XU_LY)
    hoaDon_id = Column(Integer, ForeignKey(HoaDon.__table__.c.id), nullable=False)



class BaoCaoDoanhThu(Base):

    tuNgay = Column(Date, nullable=False)
    denNgay = Column(Date, nullable=False)
    tongSoHoaDon = Column(Integer, default=0)
    tongDoanhThu = Column(Float, default=0.0)
    tongGiamGia = Column(Float, default=0.0)
    tongThue = Column(Float, default=0.0)
    tongPhiDichVu = Column(Float, default=0.0)


class TrangThaiNguyenLieuEnum(Enum):
    CON_HANG = "CON_HANG"
    SAP_HET = "SAP_HET"
    HET_HANG = "HET_HANG"
    NGUNG_SU_DUNG = "NGUNG_SU_DUNG"
class NhomNguyenLieuEnum(Enum):
    CA_PHE = "Cà phê"
    TRA = "Trà"
    SUA = "Sữa"
    DUONG = "Đường"
    TOPPING = "Topping"
    DA = "Đá"
    KHAC = "Khác"


class NguyenLieu(Base):
    congThuc = relationship("CongThuc", backref="nguyenLieu", lazy=True, cascade="all, delete-orphan")
    chiTietNhap = relationship("ChiTietPhieuNhap", backref="nguyenLieu", lazy=True)
    donViTinh = Column(String(50), nullable=False)
    soLuongTon = Column(Float, default=0.0)
    giaMuaToiThieu = Column(Float, default=0.0)
    trangThai = Column(SqlEnum(TrangThaiNguyenLieuEnum),default=TrangThaiNguyenLieuEnum.CON_HANG)
    soLuongToiThieu = Column(Float, default=5.0)
    nhom = Column(SqlEnum(NhomNguyenLieuEnum), default=NhomNguyenLieuEnum.KHAC)

    @staticmethod
    def get_active_ingredients_list():
        return NguyenLieu.query.filter(
            NguyenLieu.trangThai != TrangThaiNguyenLieuEnum.NGUNG_SU_DUNG).all()


class PhieuNhap(Base):
    chiTiet = relationship("ChiTietPhieuNhap", backref="phieuNhap", lazy=True)
    tongSoNguyenLieu = Column(Integer, default=0)
    tongGiaTriNhap = Column(Integer, default=0)
    ghiChu = Column(String(255), nullable=True)
    nguoiNhap_id = Column(Integer, ForeignKey(NhanVienCuaHang.__table__.c.id), nullable=False)

    nguoiNhap = relationship("NhanVienCuaHang", backref="phieuNhaps", foreign_keys=[nguoiNhap_id])


class ChiTietPhieuNhap(db.Model):

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=True, unique=True)
    soLuongNhap = Column(Float, nullable=False)
    donGiaNhap = Column(Float, nullable=False)
    thanhTien = Column(Float, nullable=False)

    phieuNhap_id = Column(Integer, ForeignKey(PhieuNhap.__table__.c.id), nullable=False)
    nguyenLieu_id = Column(Integer, ForeignKey(NguyenLieu.__table__.c.id), nullable=False)


class CongThuc(db.Model):

    id = Column(Integer, primary_key=True, autoincrement=True)
    dinhLuong = Column(Float, nullable=False)

    mon_id = Column(Integer, ForeignKey(Mon.__table__.c.id), nullable=False)
    nguyenLieu_id = Column(Integer, ForeignKey(NguyenLieu.__table__.c.id), nullable=False)


class LoaiQREnum(Enum):
    THANH_TOAN = "THANH_TOAN"
    HOA_DON_TAM = "HOA_DON_TAM"
    NHAP_SO_BAN = "NHAP_SO_BAN"


class TrangThaiQREnum(Enum):
    CON_HIEU_LUC = "CON_HIEU_LUC"
    HET_HIEU_LUC = "HET_HIEU_LUC"

class QRCode(db.Model):

    maQR = Column(String(255), primary_key=True, nullable=True)
    loaiQR = Column(SqlEnum(LoaiQREnum),nullable=False)
    noiDungQR = Column(String(255), nullable=False)
    ngayTao = Column(DateTime,default=datetime.datetime.now)
    trangThai = Column(SqlEnum(TrangThaiQREnum),default=TrangThaiQREnum.CON_HIEU_LUC)

    hoaDon_id = Column(Integer, ForeignKey(HoaDon.__table__.c.id), nullable=True)



class SchedulerBot(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=True)
    gioChayHangNgay = Column(Time, nullable=False, unique=True)
    trangThai = Column(SqlEnum(TrangThaiEnum),default=TrangThaiEnum.ACTIVE)
    last_run_date = Column(Date, nullable=True)


class BaoCaoTonKho(Base):

    tongSoNguyenLieu = Column(Integer, default=0)
    soNguyenLieuSapHet = Column(Integer, default=0)
    soNguyenLieuHetHang = Column(Integer, default=0)


class ThongBao(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)

    hoaDon_id = db.Column(db.Integer, db.ForeignKey(HoaDon.__table__.c.id), nullable=False, index=True)

    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    type = db.Column(db.String(50), default="TABLE_CONFIRMED", nullable=False)

    hoaDon = db.relationship("HoaDon", backref=db.backref("thongBao", lazy=True))

class TrangThaiThongBaoKhoEnum(Enum):
    UNREAD = "UNREAD"
    READ = "READ"

class LoaiThongBaoKhoEnum(Enum):
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DAILY_REPORT = "DAILY_REPORT"

class ThongBaoKho(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)

    loai = db.Column(db.Enum(LoaiThongBaoKhoEnum), default=LoaiThongBaoKhoEnum.LOW_STOCK, nullable=False)
    trang_thai = db.Column(db.Enum(TrangThaiThongBaoKhoEnum), default=TrangThaiThongBaoKhoEnum.UNREAD, nullable=False)

    message = db.Column(db.String(255), nullable=False)
    nguyenLieu_id = db.Column(db.Integer, db.ForeignKey("nguyen_lieu.id"), nullable=True, index=True)
    nguyenLieu = db.relationship("NguyenLieu")
    run_date = db.Column(db.Date, nullable=True, index=True)

Index("ix_tbk_nl_date_loai", ThongBaoKho.nguyenLieu_id, ThongBaoKho.run_date, ThongBaoKho.loai)


if __name__=="__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()