from sqlalchemy import Column, Integer,Time, String, DateTime, Enum as SqlEnum,Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from CafeApp import db
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
    matKhau = Column(String(150), nullable=True)
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
    maThamChieu = Column(String(50), unique=True, nullable=True)  # ví dụ: "HD123"
    ngayTao = Column(DateTime, default=datetime.datetime.now())



class TrangThaiMonEnum(Enum):
    DANG_BAN = "DANG_BAN"
    TAM_HET = "TAM_HET"
    NGUNG_BAN = "NGUNG_BAN"

class LoaiMonEnum(Enum):
    NUOC = "NUOC"
    BANH = "BANH"

class Mon(Base):
    chiTietHoaDon = relationship("ChiTietHoaDon", back_populates="mon", lazy=True)
    congThuc = relationship("CongThuc", backref="mon", lazy=True)
    gia = Column(Float, nullable=False)
    moTa = Column(String(255), nullable=True)
    trangThai = Column(SqlEnum(TrangThaiMonEnum), default=TrangThaiMonEnum.DANG_BAN)
    image = Column(String(255))
    loaiMon = Column(SqlEnum(LoaiMonEnum), nullable=False, default=LoaiMonEnum.NUOC)

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

class TrangThaiThanhToanEnum(Enum):
    CHO_XU_LY = "CHO_XU_LY"
    THANH_CONG = "THANH_CONG"
    THAT_BAI = "THAT_BAI"

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


class NguyenLieu(Base):
    congThuc = relationship("CongThuc", backref="nguyenLieu", lazy=True)
    chiTietNhap = relationship("ChiTietPhieuNhap", backref="nguyenLieu", lazy=True)
    donViTinh = Column(String(50), nullable=False)
    soLuongTon = Column(Float, default=0.0)
    giaMuaToiThieu = Column(Float, default=0.0)
    trangThai = Column(SqlEnum(TrangThaiNguyenLieuEnum),default=TrangThaiNguyenLieuEnum.CON_HANG)



class PhieuNhap(Base):
    chiTiet = relationship("ChiTietPhieuNhap", backref="phieuNhap", lazy=True)
    tongSoNguyenLieu = Column(Integer, default=0)
    tongGiaTriNhap = Column(Integer, default=0)
    ghiChu = Column(String(255), nullable=True)
    nguoiNhap_id = Column(Integer, ForeignKey(NhanVienCuaHang.__table__.c.id), nullable=False)



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
    gioChayHangNgay = Column(Time, nullable=False)

    trangThai = Column(SqlEnum(TrangThaiEnum),default=TrangThaiEnum.ACTIVE)

class BaoCaoTonKho(Base):

    tongSoNguyenLieu = Column(Integer, default=0)
    soNguyenLieuSapHet = Column(Integer, default=0)
    soNguyenLieuHetHang = Column(Integer, default=0)

# if __name__=="__main__":
#     with app.app_context():
#         db.drop_all()
#         db.create_all()