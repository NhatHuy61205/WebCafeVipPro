import random
import datetime
from app import app, db
from models import *

def seed_data():
    with app.app_context():

        db.drop_all()
        db.create_all()

        # ======================
        # NHÂN VIÊN (10)
        # ======================
        nhanviens = []
        roles = list(RoleEnum)
        for i in range(1, 11):
            nv = NhanVienCuaHang(
                name=f"Nhân viên {i}",
                sdt=f"09000000{i:02}",
                tenDangNhap=f"nv{i}",
                matKhau="123456",
                role=random.choice(roles),
                trangThai=TrangThaiEnum.ACTIVE
            )
            nhanviens.append(nv)
        db.session.add_all(nhanviens)
        db.session.commit()

        # ======================
        # KHÁCH HÀNG (15)
        # ======================
        khachhangs = []
        loais = list(LoaiDungEnum)
        for i in range(1, 16):
            kh = KhachHang(
                name=f"Khách hàng {i}",
                sdt=f"09100000{i:02}",
                diaChi="TP.HCM" if i % 2 == 0 else None,
                tongDonHangDaMua=random.randint(0, 20),
                loaiKhachHang=random.choice(loais),
                email=f"kh{i}@gmail.com"
            )
            khachhangs.append(kh)
        db.session.add_all(khachhangs)
        db.session.commit()

        # ======================
        # MÓN (15)
        # ======================
        mons = []
        for i in range(1, 16):
            m = Mon(
                name=f"Món {i}",
                gia=random.randint(20000, 60000),
                moTa="Món uống phổ biến",
                trangThai=TrangThaiMonEnum.DANG_BAN,
                image=f"mon_{i}.jpg"
            )
            mons.append(m)
        db.session.add_all(mons)
        db.session.commit()

        # ======================
        # HÓA ĐƠN (15)
        # ======================
        hoadons = []
        for i in range(1, 16):
            hd = HoaDon(
                name=f"Hóa đơn {i}",
                ngayThanhToan=datetime.datetime.now(),
                soBan=random.randint(1, 20),
                tongTienHang=0,
                thue=0,
                phiPhucVu=0,
                giamGia=0,
                tongThanhToan=0,
                loaiHoaDon=random.choice(loais),
                trangThai=random.choice(list(TrangThaiHoaDonEnum)),
                khachHang_id=random.choice(khachhangs).id
            )
            hoadons.append(hd)
        db.session.add_all(hoadons)
        db.session.commit()

        # ======================
        # CHI TIẾT HÓA ĐƠN (30)
        # ======================
        for hd in hoadons:
            for _ in range(random.randint(1, 3)):
                mon = random.choice(mons)
                sl = random.randint(1, 3)
                ct = ChiTietHoaDon(
                    soLuong=sl,
                    donGia=mon.gia,
                    thanhTien=sl * mon.gia,
                    ghiChu=None,
                    hoaDon_id=hd.id,
                    mon_id=mon.id
                )
                hd.tongTienHang += ct.thanhTien
                db.session.add(ct)

            hd.thue = hd.tongTienHang * 0.1
            hd.phiPhucVu = hd.tongTienHang * 0.05
            hd.tongThanhToan = hd.tongTienHang + hd.thue + hd.phiPhucVu

        db.session.commit()

        # ======================
        # THANH TOÁN (15)
        # ======================
        for hd in hoadons:
            tt = ThanhToan(
                name=f"TT-HD-{hd.id}",
                soTien=hd.tongThanhToan,
                trangThai=TrangThaiThanhToanEnum.THANH_CONG,
                hoaDon_id=hd.id
            )
            db.session.add(tt)
        db.session.commit()

        # ======================
        # NGUYÊN LIỆU (15)
        # ======================
        nguyenlieus = []
        for i in range(1, 16):
            nl = NguyenLieu(
                name=f"Nguyên liệu {i}",
                donViTinh="g",
                soLuongTon=random.randint(1000, 5000),
                giaMuaToiThieu=random.randint(500, 2000),
                trangThai=TrangThaiNguyenLieuEnum.CON_HANG
            )
            nguyenlieus.append(nl)
        db.session.add_all(nguyenlieus)
        db.session.commit()

        # ======================
        # CÔNG THỨC (30)
        # ======================
        for mon in mons:
            for _ in range(2):
                ct = CongThuc(
                    dinhLuong=random.randint(10, 50),
                    mon_id=mon.id,
                    nguyenLieu_id=random.choice(nguyenlieus).id
                )
                db.session.add(ct)
        db.session.commit()

        # ======================
        # PHIẾU NHẬP (10)
        # ======================
        phieunhaps = []
        for i in range(1, 11):
            pn = PhieuNhap(
                name=f"Phiếu nhập {i}",
                tongSoNguyenLieu=0,
                tongGiaTriNhap=0,
                ghiChu="Nhập kho",
                nguoiNhap_id=random.choice(nhanviens).id
            )
            phieunhaps.append(pn)
        db.session.add_all(phieunhaps)
        db.session.commit()

        # ======================
        # CHI TIẾT PHIẾU NHẬP (20)
        # ======================
        for pn in phieunhaps:
            for _ in range(2):
                nl = random.choice(nguyenlieus)
                sl = random.randint(50, 200)
                dg = random.randint(1000, 3000)
                ctpn = ChiTietPhieuNhap(
                    soLuongNhap=sl,
                    donGiaNhap=dg,
                    thanhTien=sl * dg,
                    phieuNhap_id=pn.id,
                    nguyenLieu_id=nl.id
                )
                pn.tongSoNguyenLieu += 1
                pn.tongGiaTriNhap += ctpn.thanhTien
                db.session.add(ctpn)
        db.session.commit()

        # ======================
        # QR CODE (15)
        # ======================
        for hd in hoadons:
            qr = QRCode(
                maQR=f"QR_HD_{hd.id}",
                loaiQR=LoaiQREnum.THANH_TOAN,
                noiDungQR=f"Thanh toán hóa đơn {hd.id}",
                trangThai=TrangThaiQREnum.CON_HIEU_LUC,
                hoaDon_id=hd.id
            )
            db.session.add(qr)
        db.session.commit()

        # ======================
        # SCHEDULER (1)
        # ======================
        scheduler = SchedulerBot(
            gioChayHangNgay=datetime.time(23, 0),
            trangThai=TrangThaiEnum.ACTIVE
        )
        db.session.add(scheduler)

        # ======================
        # BÁO CÁO
        # ======================
        bc1 = BaoCaoDoanhThu(
            name="Báo cáo tháng",
            tuNgay=datetime.date.today() - datetime.timedelta(days=30),
            denNgay=datetime.date.today(),
            tongSoHoaDon=len(hoadons),
            tongDoanhThu=sum(h.tongThanhToan for h in hoadons),
            tongThue=sum(h.thue for h in hoadons),
            tongPhiDichVu=sum(h.phiPhucVu for h in hoadons),
            tongGiamGia=0
        )

        bc2 = BaoCaoTonKho(
            name="Báo cáo tồn kho",
            tongSoNguyenLieu=len(nguyenlieus),
            soNguyenLieuSapHet=2,
            soNguyenLieuHetHang=0
        )

        db.session.add_all([bc1, bc2])
        db.session.commit()


if __name__ == "__main__":
    seed_data()
