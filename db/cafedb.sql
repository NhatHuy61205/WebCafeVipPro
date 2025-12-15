-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: cafedb
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bao_cao_doanh_thu`
--

DROP TABLE IF EXISTS `bao_cao_doanh_thu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bao_cao_doanh_thu` (
  `tuNgay` date NOT NULL,
  `denNgay` date NOT NULL,
  `tongSoHoaDon` int DEFAULT NULL,
  `tongDoanhThu` float DEFAULT NULL,
  `tongGiamGia` float DEFAULT NULL,
  `tongThue` float DEFAULT NULL,
  `tongPhiDichVu` float DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bao_cao_ton_kho`
--

DROP TABLE IF EXISTS `bao_cao_ton_kho`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bao_cao_ton_kho` (
  `tongSoNguyenLieu` int DEFAULT NULL,
  `soNguyenLieuSapHet` int DEFAULT NULL,
  `soNguyenLieuHetHang` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chi_tiet_hoa_don`
--

DROP TABLE IF EXISTS `chi_tiet_hoa_don`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chi_tiet_hoa_don` (
  `id` int NOT NULL AUTO_INCREMENT,
  `soLuong` int NOT NULL,
  `donGia` float NOT NULL,
  `thanhTien` float NOT NULL,
  `ghiChu` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hoaDon_id` int NOT NULL,
  `mon_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `hoaDon_id` (`hoaDon_id`),
  KEY `mon_id` (`mon_id`),
  CONSTRAINT `chi_tiet_hoa_don_ibfk_1` FOREIGN KEY (`hoaDon_id`) REFERENCES `hoa_don` (`id`),
  CONSTRAINT `chi_tiet_hoa_don_ibfk_2` FOREIGN KEY (`mon_id`) REFERENCES `mon` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chi_tiet_phieu_nhap`
--

DROP TABLE IF EXISTS `chi_tiet_phieu_nhap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chi_tiet_phieu_nhap` (
  `id` int NOT NULL AUTO_INCREMENT,
  `soLuongNhap` float NOT NULL,
  `donGiaNhap` float NOT NULL,
  `thanhTien` float NOT NULL,
  `phieuNhap_id` int NOT NULL,
  `nguyenLieu_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `phieuNhap_id` (`phieuNhap_id`),
  KEY `nguyenLieu_id` (`nguyenLieu_id`),
  CONSTRAINT `chi_tiet_phieu_nhap_ibfk_1` FOREIGN KEY (`phieuNhap_id`) REFERENCES `phieu_nhap` (`id`),
  CONSTRAINT `chi_tiet_phieu_nhap_ibfk_2` FOREIGN KEY (`nguyenLieu_id`) REFERENCES `nguyen_lieu` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cong_thuc`
--

DROP TABLE IF EXISTS `cong_thuc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cong_thuc` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dinhLuong` float NOT NULL,
  `mon_id` int NOT NULL,
  `nguyenLieu_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `mon_id` (`mon_id`),
  KEY `nguyenLieu_id` (`nguyenLieu_id`),
  CONSTRAINT `cong_thuc_ibfk_1` FOREIGN KEY (`mon_id`) REFERENCES `mon` (`id`),
  CONSTRAINT `cong_thuc_ibfk_2` FOREIGN KEY (`nguyenLieu_id`) REFERENCES `nguyen_lieu` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hoa_don`
--

DROP TABLE IF EXISTS `hoa_don`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hoa_don` (
  `ngayThanhToan` datetime DEFAULT NULL,
  `soBan` int DEFAULT NULL,
  `tongTienHang` float DEFAULT NULL,
  `thue` float DEFAULT NULL,
  `phiPhucVu` float DEFAULT NULL,
  `giamGia` float DEFAULT NULL,
  `tongThanhToan` float DEFAULT NULL,
  `loaiHoaDon` enum('TAI_QUAN','TAI_NHA','MANG_DI') COLLATE utf8mb4_unicode_ci NOT NULL,
  `trangThai` enum('TAM','CHO_THANH_TOAN','DA_THANH_TOAN','DANG_CHE_BIEN','HOAN_THANH') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `khachHang_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `khachHang_id` (`khachHang_id`),
  CONSTRAINT `hoa_don_ibfk_1` FOREIGN KEY (`khachHang_id`) REFERENCES `khach_hang` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `khach_hang`
--

DROP TABLE IF EXISTS `khach_hang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `khach_hang` (
  `sdt` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `diaChi` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tongDonHangDaMua` int DEFAULT NULL,
  `loaiKhachHang` enum('TAI_QUAN','TAI_NHA','MANG_DI') COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sdt` (`sdt`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mon`
--

DROP TABLE IF EXISTS `mon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mon` (
  `gia` float NOT NULL,
  `moTa` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trangThai` enum('DANG_BAN','TAM_HET','NGUNG_BAN') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nguyen_lieu`
--

DROP TABLE IF EXISTS `nguyen_lieu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nguyen_lieu` (
  `donViTinh` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `soLuongTon` float DEFAULT NULL,
  `giaMuaToiThieu` float DEFAULT NULL,
  `trangThai` enum('CON_HANG','SAP_HET','HET_HANG') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nhan_vien_cua_hang`
--

DROP TABLE IF EXISTS `nhan_vien_cua_hang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nhan_vien_cua_hang` (
  `sdt` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tenDangNhap` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `matKhau` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` enum('NHAN_VIEN','QUAN_LY_KHO','QUAN_LY_CUA_HANG') COLLATE utf8mb4_unicode_ci NOT NULL,
  `trangThai` enum('ACTIVE','INACTIVE') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sdt` (`sdt`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `tenDangNhap` (`tenDangNhap`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `phieu_nhap`
--

DROP TABLE IF EXISTS `phieu_nhap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `phieu_nhap` (
  `tongSoNguyenLieu` int DEFAULT NULL,
  `tongGiaTriNhap` int DEFAULT NULL,
  `ghiChu` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nguoiNhap_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `nguoiNhap_id` (`nguoiNhap_id`),
  CONSTRAINT `phieu_nhap_ibfk_1` FOREIGN KEY (`nguoiNhap_id`) REFERENCES `nhan_vien_cua_hang` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `qr_code`
--

DROP TABLE IF EXISTS `qr_code`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qr_code` (
  `maQR` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `loaiQR` enum('THANH_TOAN','HOA_DON_TAM','NHAP_SO_BAN') COLLATE utf8mb4_unicode_ci NOT NULL,
  `noiDungQR` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  `trangThai` enum('CON_HIEU_LUC','HET_HIEU_LUC') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hoaDon_id` int DEFAULT NULL,
  PRIMARY KEY (`maQR`),
  KEY `hoaDon_id` (`hoaDon_id`),
  CONSTRAINT `qr_code_ibfk_1` FOREIGN KEY (`hoaDon_id`) REFERENCES `hoa_don` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduler_bot`
--

DROP TABLE IF EXISTS `scheduler_bot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scheduler_bot` (
  `id` int NOT NULL AUTO_INCREMENT,
  `gioChayHangNgay` time NOT NULL,
  `trangThai` enum('ACTIVE','INACTIVE') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `thanh_toan`
--

DROP TABLE IF EXISTS `thanh_toan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thanh_toan` (
  `soTien` float NOT NULL,
  `trangThai` enum('CHO_XU_LY','THANH_CONG','THAT_BAI') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hoaDon_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ngayTao` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `hoaDon_id` (`hoaDon_id`),
  CONSTRAINT `thanh_toan_ibfk_1` FOREIGN KEY (`hoaDon_id`) REFERENCES `hoa_don` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-15 18:32:48
