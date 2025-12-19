
import datetime
import random

from CafeApp import app, db
from models import (
    NhanVienCuaHang, KhachHang, Mon, HoaDon, ChiTietHoaDon, ThanhToan,
    NguyenLieu, PhieuNhap, ChiTietPhieuNhap, CongThuc, QRCode, SchedulerBot,
    BaoCaoDoanhThu, BaoCaoTonKho,
    RoleEnum, TrangThaiEnum, LoaiDungEnum, TrangThaiHoaDonEnum,
    TrangThaiMonEnum, LoaiMonEnum, SizeEnum,
    TrangThaiThanhToanEnum, TrangThaiNguyenLieuEnum,
    LoaiQREnum, TrangThaiQREnum, Topping, MonTopping, ChiTietHoaDonTopping
)

def seed_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        random.seed(42)

        # ======================
        # NHÂN VIÊN (10)
        # ======================
        nhanviens = [
            NhanVienCuaHang(name="Nguyễn Minh An", sdt="0900000001", tenDangNhap="nv01", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Trần Thị Bảo", sdt="0900000002", tenDangNhap="nv02", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Lê Quốc Cường", sdt="0900000003", tenDangNhap="nv03", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Phạm Gia Duy", sdt="0900000004", tenDangNhap="nv04", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Võ Thanh Hằng", sdt="0900000005", tenDangNhap="nv05", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Đặng Nhật Huy", sdt="0900000006", tenDangNhap="nv06", matKhau="123456", role=RoleEnum.QUAN_LY_KHO, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Ngô Thiên Kỳ", sdt="0900000007", tenDangNhap="nv07", matKhau="123456", role=RoleEnum.QUAN_LY_KHO, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Bùi Thảo Linh", sdt="0900000008", tenDangNhap="nv08", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.ACTIVE),
            NhanVienCuaHang(name="Đỗ Khánh Mai", sdt="0900000009", tenDangNhap="nv09", matKhau="123456", role=RoleEnum.NHAN_VIEN, trangThai=TrangThaiEnum.INACTIVE),
            NhanVienCuaHang(name="Hoàng Gia Nam", sdt="0900000010", tenDangNhap="nv10", matKhau="123456", role=RoleEnum.QUAN_LY_CUA_HANG, trangThai=TrangThaiEnum.ACTIVE),
        ]
        db.session.add_all(nhanviens)
        db.session.commit()

        # ======================
        # KHÁCH HÀNG (10)
        # ======================
        khachhangs = [
            KhachHang(name="Khách A", sdt="0911111101", diaChi="Quận 1, TP.HCM", tongDonHangDaMua=2, loaiKhachHang=LoaiDungEnum.TAI_NHA, email="kh01@gmail.com"),
            KhachHang(name="Khách B", sdt="0911111102", diaChi=None, tongDonHangDaMua=0, loaiKhachHang=LoaiDungEnum.TAI_QUAN, email="kh02@gmail.com"),
            KhachHang(name="Khách C", sdt="0911111103", diaChi="Quận 7, TP.HCM", tongDonHangDaMua=5, loaiKhachHang=LoaiDungEnum.TAI_NHA, email="kh03@gmail.com"),
            KhachHang(name="Khách D", sdt="0911111104", diaChi=None, tongDonHangDaMua=1, loaiKhachHang=LoaiDungEnum.MANG_DI, email="kh04@gmail.com"),
            KhachHang(name="Khách E", sdt="0911111105", diaChi="Thủ Đức, TP.HCM", tongDonHangDaMua=8, loaiKhachHang=LoaiDungEnum.TAI_NHA, email="kh05@gmail.com"),
            KhachHang(name="Khách F", sdt="0911111106", diaChi=None, tongDonHangDaMua=3, loaiKhachHang=LoaiDungEnum.TAI_QUAN, email="kh06@gmail.com"),
            KhachHang(name="Khách G", sdt="0911111107", diaChi="Bình Thạnh, TP.HCM", tongDonHangDaMua=12, loaiKhachHang=LoaiDungEnum.TAI_NHA, email="kh07@gmail.com"),
            KhachHang(name="Khách H", sdt="0911111108", diaChi=None, tongDonHangDaMua=0, loaiKhachHang=LoaiDungEnum.MANG_DI, email="kh08@gmail.com"),
            KhachHang(name="Khách I", sdt="0911111109", diaChi="Gò Vấp, TP.HCM", tongDonHangDaMua=4, loaiKhachHang=LoaiDungEnum.TAI_NHA, email="kh09@gmail.com"),
            KhachHang(name="Khách J", sdt="0911111110", diaChi=None, tongDonHangDaMua=7, loaiKhachHang=LoaiDungEnum.TAI_QUAN, email="kh10@gmail.com"),
        ]
        db.session.add_all(khachhangs)
        db.session.commit()

        # ======================
        # MÓN (15) - gồm NƯỚC & BÁNH
        # ======================
        mons = [
            Mon(name="Trà sữa truyền thống", gia=35000, moTa="Trà sữa", trangThai=TrangThaiMonEnum.DANG_BAN, image="tra_sua_tt.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Trà đào cam sả", gia=42000, moTa="Trà trái cây", trangThai=TrangThaiMonEnum.DANG_BAN, image="tra_dao.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Cà phê sữa", gia=30000, moTa="Cà phê", trangThai=TrangThaiMonEnum.DANG_BAN, image="cf_sua.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Bạc xỉu", gia=32000, moTa="Cà phê", trangThai=TrangThaiMonEnum.DANG_BAN, image="bac_xiu.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Matcha latte", gia=45000, moTa="Matcha", trangThai=TrangThaiMonEnum.DANG_BAN, image="matcha.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Soda việt quất", gia=39000, moTa="Soda", trangThai=TrangThaiMonEnum.DANG_BAN, image="soda_vq.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Nước cam", gia=35000, moTa="Nước ép", trangThai=TrangThaiMonEnum.DANG_BAN, image="cam.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Chanh dây đá xay", gia=47000, moTa="Đá xay", trangThai=TrangThaiMonEnum.DANG_BAN, image="chanh_day.jpg", loaiMon=LoaiMonEnum.NUOC),
            Mon(name="Hồng trà sữa", gia=38000, moTa="Trà sữa", trangThai=TrangThaiMonEnum.DANG_BAN, image="hong_tra.jpg", loaiMon=LoaiMonEnum.NUOC),

            Mon(name="Bánh tiramisu", gia=55000, moTa="Bánh ngọt", trangThai=TrangThaiMonEnum.DANG_BAN, image="tiramisu.jpg", loaiMon=LoaiMonEnum.BANH),
            Mon(name="Bánh su kem", gia=25000, moTa="Bánh ngọt", trangThai=TrangThaiMonEnum.DANG_BAN, image="su_kem.jpg", loaiMon=LoaiMonEnum.BANH),
            Mon(name="Bánh croissant", gia=28000, moTa="Bánh mặn", trangThai=TrangThaiMonEnum.DANG_BAN, image="croissant.jpg", loaiMon=LoaiMonEnum.BANH),
            Mon(name="Bánh brownie", gia=42000, moTa="Bánh ngọt", trangThai=TrangThaiMonEnum.DANG_BAN, image="brownie.jpg", loaiMon=LoaiMonEnum.BANH),
            Mon(name="Bánh flan", gia=20000, moTa="Tráng miệng", trangThai=TrangThaiMonEnum.DANG_BAN, image="flan.jpg", loaiMon=LoaiMonEnum.BANH),
            Mon(name="Bánh phô mai", gia=48000, moTa="Cheesecake", trangThai=TrangThaiMonEnum.TAM_HET, image="cheesecake.jpg", loaiMon=LoaiMonEnum.BANH),
        ]
        db.session.add_all(mons)
        db.session.commit()
        # ======================
        # TOPPING (6)
        # ======================
        toppings = [
            Topping(name="Trân châu", code="TRAN_CHAU", price=5000),
            Topping(name="Pudding", code="PUDDING", price=7000),
            Topping(name="Kem cheese", code="KEM_CHEESE", price=10000),
            Topping(name="Thạch cà phê", code="THACH_CF", price=6000),
            Topping(name="Thạch trái cây", code="THACH_TC", price=6000),
            Topping(name="Trân châu trắng", code="TRAN_CHAU_TRANG", price=5500),
        ]
        db.session.add_all(toppings)
        db.session.commit()
        # ======================
        # MON - TOPPING (Mapping)
        # ======================
        mon_nuoc = [m for m in mons if m.loaiMon == LoaiMonEnum.NUOC]
        mon_banh = [m for m in mons if m.loaiMon == LoaiMonEnum.BANH]

        mon_toppings = []

        for mon in mon_nuoc:
            # tất cả món nước đều có trân châu + pudding
            mon_toppings.append(
                MonTopping(mon_id=mon.id, topping_id=toppings[0].id)  # TRAN_CHAU
            )
            mon_toppings.append(
                MonTopping(mon_id=mon.id, topping_id=toppings[1].id)  # PUDDING
            )

        # riêng Matcha latte có kem cheese (giá override)
        matcha = next((m for m in mon_nuoc if "Matcha" in m.name), None)
        if matcha:
            mon_toppings.append(
                MonTopping(
                    mon_id=matcha.id,
                    topping_id=toppings[2].id,  # KEM_CHEESE
                    override_price=9000
                )
            )

        # bánh KHÔNG cho topping
        for mon in mon_banh:
            mon_toppings.append(
                MonTopping(
                    mon_id=mon.id,
                    topping_id=toppings[0].id,
                    is_allowed=False
                )
            )

        db.session.add_all(mon_toppings)
        db.session.commit()

        # ======================
        # NGUYÊN LIỆU (15)
        # ======================
        nguyenlieus = [
            NguyenLieu(name="Hạt cà phê", donViTinh="g", soLuongTon=5000, giaMuaToiThieu=1200, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Sữa đặc", donViTinh="ml", soLuongTon=8000, giaMuaToiThieu=15, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Sữa tươi", donViTinh="ml", soLuongTon=6000, giaMuaToiThieu=18, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Trà đen", donViTinh="g", soLuongTon=3000, giaMuaToiThieu=900, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Trà xanh", donViTinh="g", soLuongTon=2500, giaMuaToiThieu=950, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Bột matcha", donViTinh="g", soLuongTon=1200, giaMuaToiThieu=2200, trangThai=TrangThaiNguyenLieuEnum.SAP_HET),
            NguyenLieu(name="Đường", donViTinh="g", soLuongTon=9000, giaMuaToiThieu=30, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Đá viên", donViTinh="g", soLuongTon=20000, giaMuaToiThieu=2, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Cam tươi", donViTinh="g", soLuongTon=4000, giaMuaToiThieu=40, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Chanh dây", donViTinh="g", soLuongTon=1800, giaMuaToiThieu=55, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Bột cacao", donViTinh="g", soLuongTon=1400, giaMuaToiThieu=1700, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Bánh mì", donViTinh="cái", soLuongTon=200, giaMuaToiThieu=6000, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
            NguyenLieu(name="Kem tươi", donViTinh="ml", soLuongTon=900, giaMuaToiThieu=25, trangThai=TrangThaiNguyenLieuEnum.SAP_HET),
            NguyenLieu(name="Phô mai", donViTinh="g", soLuongTon=700, giaMuaToiThieu=60, trangThai=TrangThaiNguyenLieuEnum.SAP_HET),
            NguyenLieu(name="Trứng gà", donViTinh="quả", soLuongTon=120, giaMuaToiThieu=3500, trangThai=TrangThaiNguyenLieuEnum.CON_HANG),
        ]
        db.session.add_all(nguyenlieus)
        db.session.commit()

        # ======================
        # CÔNG THỨC (30) - mỗi món nước/bánh có 2 nguyên liệu
        # ======================
        congthucs = []
        for i, mon in enumerate(mons):
            # chọn 2 nguyên liệu khác nhau
            nl1 = nguyenlieus[(i * 2) % len(nguyenlieus)]
            nl2 = nguyenlieus[(i * 2 + 1) % len(nguyenlieus)]
            congthucs.append(CongThuc(dinhLuong=20 + (i % 5) * 5, mon_id=mon.id, nguyenLieu_id=nl1.id))
            congthucs.append(CongThuc(dinhLuong=10 + (i % 3) * 5, mon_id=mon.id, nguyenLieu_id=nl2.id))
        # 15 món * 2 = 30
        db.session.add_all(congthucs)
        db.session.commit()

        # ======================
        # HÓA ĐƠN (12)
        # ======================
        hoadons = []
        loais = [LoaiDungEnum.TAI_QUAN, LoaiDungEnum.TAI_NHA, LoaiDungEnum.MANG_DI]
        trangthais = [
            TrangThaiHoaDonEnum.DA_THANH_TOAN,
            TrangThaiHoaDonEnum.CHO_THANH_TOAN,
            TrangThaiHoaDonEnum.HUY
        ]
        now = datetime.datetime.now()

        for i in range(1, 13):
            loai = loais[(i - 1) % len(loais)]
            tt = trangthais[(i - 1) % len(trangthais)]

            ngay_tao = now - datetime.timedelta(hours=i)
            ngay_thanh_toan = (
                        now - datetime.timedelta(hours=i - 1)) if tt == TrangThaiHoaDonEnum.DA_THANH_TOAN else None

            hd = HoaDon(
                name=f"HD{i:03}",

                # ✅ field mới
                ngayTao=ngay_tao,
                ngayThanhToan=ngay_thanh_toan,
                maThamChieu=None,  # set sau khi commit để dùng id

                soBan=(i % 10) + 1 if loai == LoaiDungEnum.TAI_QUAN else None,

                tongTienHang=0.0,
                thue=0.0,
                phiPhucVu=0.0,
                giamGia=0.0,
                tongThanhToan=0.0,

                loaiHoaDon=loai,
                trangThai=tt,

                khachHang_id=khachhangs[(i - 1) % len(khachhangs)].id
            )
            hoadons.append(hd)

        db.session.add_all(hoadons)
        db.session.commit()


        for hd in hoadons:
            hd.maThamChieu = f"HD{hd.id}"

        db.session.commit()

        # ======================
        # CHI TIẾT HÓA ĐƠN (~24)
        # ======================
        chi_tiets = []
        sizes = [SizeEnum.S, SizeEnum.M, SizeEnum.L]
        duongs = [0, 30, 50, 70, 100]
        das = [0, 30, 50, 70, 100]

        for i, hd in enumerate(hoadons):
            # mỗi hóa đơn 2 dòng
            for j in range(2):
                mon = mons[(i * 2 + j) % len(mons)]
                sl = 1 + ((i + j) % 3)

                # Nếu là bánh -> không dùng đường/đá (set 0 cho rõ ràng)
                if mon.loaiMon == LoaiMonEnum.BANH:
                    muc_duong = 0
                    muc_da = 0
                    size = SizeEnum.S
                else:
                    muc_duong = duongs[(i + j) % len(duongs)]
                    muc_da = das[(i * 2 + j) % len(das)]
                    size = sizes[(i + j) % len(sizes)]

                don_gia = float(mon.gia)
                thanh_tien = don_gia * sl

                ct = ChiTietHoaDon(
                    soLuong=sl,
                    donGia=don_gia,
                    thanhTien=thanh_tien,
                    ghiChu="Ít ngọt" if (mon.loaiMon == LoaiMonEnum.NUOC and muc_duong <= 50) else None,
                    size=size,
                    mucDuong=muc_duong,
                    mucDa=muc_da,
                    hoaDon_id=hd.id,
                    mon_id=mon.id
                )
                chi_tiets.append(ct)
                hd.tongTienHang += thanh_tien

            # tính thuế + phí phục vụ theo mô hình bạn đang dùng
            hd.thue = round(hd.tongTienHang * 0.1, 2)
            hd.phiPhucVu = round(hd.tongTienHang * 0.05, 2)
            hd.tongThanhToan = round(hd.tongTienHang + hd.thue + hd.phiPhucVu - hd.giamGia, 2)

        db.session.add_all(chi_tiets)
        db.session.commit()
        db.session.add_all(hoadons)
        db.session.commit()

        # ======================
        # THANH TOÁN (12) - tạo cho tất cả hóa đơn
        # ======================
        thanhtoans = []

        for hd in hoadons:
            if hd.trangThai == TrangThaiHoaDonEnum.DA_THANH_TOAN:
                st = TrangThaiThanhToanEnum.THANH_CONG
            elif hd.trangThai == TrangThaiHoaDonEnum.CHO_THANH_TOAN:
                st = TrangThaiThanhToanEnum.CHO_XU_LY
            else:
                st = TrangThaiThanhToanEnum.THAT_BAI

            thanhtoans.append(
                ThanhToan(
                    name=f"TT_HD{hd.id}",  # ✅ ổn định theo id
                    soTien=hd.tongThanhToan,
                    trangThai=st,
                    hoaDon_id=hd.id,

                    # ✅ nếu class ThanhToan của bạn có field này thì dùng:
                    # maThamChieu=hd.maThamChieu
                )
            )

        db.session.add_all(thanhtoans)
        db.session.commit()

        # ======================
        # PHIẾU NHẬP (10)
        # ======================
        phieunhaps = []
        for i in range(1, 11):
            pn = PhieuNhap(
                name=f"PN{i:03}",
                tongSoNguyenLieu=0,
                tongGiaTriNhap=0,
                ghiChu="Nhập kho định kỳ",
                nguoiNhap_id=nhanviens[(i - 1) % len(nhanviens)].id
            )
            phieunhaps.append(pn)
        db.session.add_all(phieunhaps)
        db.session.commit()

        # ======================
        # CHI TIẾT PHIẾU NHẬP (20) - mỗi phiếu 2 dòng
        # ======================
        chitiet_nhaps = []
        for i, pn in enumerate(phieunhaps):
            for j in range(2):
                nl = nguyenlieus[(i * 2 + j) % len(nguyenlieus)]
                sl = 100 + (i * 10) + (j * 25)
                dg = 1000 + (i * 50) + (j * 100)
                tt = float(sl * dg)

                ctpn = ChiTietPhieuNhap(
                    soLuongNhap=float(sl),
                    donGiaNhap=float(dg),
                    thanhTien=tt,
                    phieuNhap_id=pn.id,
                    nguyenLieu_id=nl.id
                )
                chitiet_nhaps.append(ctpn)
                pn.tongSoNguyenLieu += 1
                pn.tongGiaTriNhap += tt

        db.session.add_all(chitiet_nhaps)
        db.session.commit()
        db.session.add_all(phieunhaps)
        db.session.commit()

        # ======================
        # QR CODE (12) - mỗi hóa đơn 1 QR thanh toán
        # ======================
        qrs = []
        for hd in hoadons:
            qrs.append(
                QRCode(
                    maQR=f"QR_{hd.name}",
                    loaiQR=LoaiQREnum.THANH_TOAN,
                    noiDungQR=f"Thanh toán {hd.name}",
                    trangThai=TrangThaiQREnum.CON_HIEU_LUC,
                    hoaDon_id=hd.id
                )
            )
        db.session.add_all(qrs)
        db.session.commit()

        # ======================
        # SCHEDULER (1)
        # ======================
        scheduler = SchedulerBot(
            gioChayHangNgay=datetime.time(23, 0),
            trangThai=TrangThaiEnum.ACTIVE
        )
        db.session.add(scheduler)
        db.session.commit()
        # ======================
        # CHI TIẾT HÓA ĐƠN - TOPPING
        # ======================
        cthd_toppings = []

        # chỉ gán topping cho CHI TIẾT MÓN NƯỚC
        chi_tiet_nuoc = [
            ct for ct in chi_tiets
            if ct.mon.loaiMon == LoaiMonEnum.NUOC
        ]

        for i, ct in enumerate(chi_tiet_nuoc[:10]):  # lấy 10 dòng đầu để test
            # mỗi dòng chọn 1–2 topping
            t1 = toppings[i % len(toppings)]
            cthd_toppings.append(
                ChiTietHoaDonTopping(
                    chi_tiet_hoa_don_id=ct.id,
                    topping_id=t1.id,
                    qty=1,
                    price_at_time=t1.price
                )
            )

            # dòng chẵn thì thêm topping thứ 2
            if i % 2 == 0:
                t2 = toppings[(i + 1) % len(toppings)]
                cthd_toppings.append(
                    ChiTietHoaDonTopping(
                        chi_tiet_hoa_don_id=ct.id,
                        topping_id=t2.id,
                        qty=1,
                        price_at_time=t2.price
                    )
                )

        db.session.add_all(cthd_toppings)
        db.session.commit()

        # ======================
        # BÁO CÁO (Doanh thu: 3, Tồn kho: 1)
        # ======================
        today = datetime.date.today()
        bc_doanh_thu = [
            BaoCaoDoanhThu(
                name="Báo cáo 7 ngày",
                tuNgay=today - datetime.timedelta(days=7),
                denNgay=today,
                tongSoHoaDon=len(hoadons),
                tongDoanhThu=sum(h.tongThanhToan for h in hoadons),
                tongGiamGia=sum(h.giamGia for h in hoadons),
                tongThue=sum(h.thue for h in hoadons),
                tongPhiDichVu=sum(h.phiPhucVu for h in hoadons),
            ),
            BaoCaoDoanhThu(
                name="Báo cáo 30 ngày",
                tuNgay=today - datetime.timedelta(days=30),
                denNgay=today,
                tongSoHoaDon=len(hoadons),
                tongDoanhThu=sum(h.tongThanhToan for h in hoadons),
                tongGiamGia=sum(h.giamGia for h in hoadons),
                tongThue=sum(h.thue for h in hoadons),
                tongPhiDichVu=sum(h.phiPhucVu for h in hoadons),
            ),
            BaoCaoDoanhThu(
                name="Báo cáo tháng hiện tại",
                tuNgay=today.replace(day=1),
                denNgay=today,
                tongSoHoaDon=len(hoadons),
                tongDoanhThu=sum(h.tongThanhToan for h in hoadons),
                tongGiamGia=sum(h.giamGia for h in hoadons),
                tongThue=sum(h.thue for h in hoadons),
                tongPhiDichVu=sum(h.phiPhucVu for h in hoadons),
            )
        ]
        db.session.add_all(bc_doanh_thu)

        bc_tonkho = BaoCaoTonKho(
            name="Báo cáo tồn kho",
            tongSoNguyenLieu=len(nguyenlieus),
            soNguyenLieuSapHet=sum(1 for nl in nguyenlieus if nl.trangThai == TrangThaiNguyenLieuEnum.SAP_HET),
            soNguyenLieuHetHang=sum(1 for nl in nguyenlieus if nl.trangThai == TrangThaiNguyenLieuEnum.HET_HANG),
        )
        db.session.add(bc_tonkho)
        db.session.commit()



if __name__ == "__main__":
    seed_data()
