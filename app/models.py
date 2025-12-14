from sqlalchemy import Column, Integer, String, DateTime, Enum as SqlEnum, Boolean
from app import db
import datetime
from enum import Enum

class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

    created_date = Column(
        DateTime,
        default=datetime.datetime.now
    )
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name


class RoleEnum(Enum):
    NHAN_VIEN = "NHAN_VIEN"
    QUAN_LY_KHO = "QUAN_LY_KHO"
    QUAN_LY_CUA_HANG = "QUAN_LY_CUA_HANG"


class TrangThaiEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class NhanVienCuaHang(Base):
    __abstract__ = True

    ten = Column(String(150), nullable=False)

    sdt = Column(String(20), nullable=False, unique=True)

    tenDangNhap = Column(String(100), nullable=False, unique=True)

    matKhau = Column(String(150), nullable=False)

    ngayTao = Column(
        DateTime,
        default=datetime.datetime.now
    )

    role = Column(
        SqlEnum(RoleEnum),
        nullable=False
    )

    trangThai = Column(
        SqlEnum(TrangThaiEnum),
        default=TrangThaiEnum.ACTIVE
    )