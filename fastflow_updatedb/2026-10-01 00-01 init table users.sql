-- =====================================================================
-- Seed FastFlow: table users + akun admin awal
-- Struktur kolom, tipe, default, komentar & index SAMA dengan table users pada sistem ERP asal seed ini
-- (diambil dari SHOW CREATE TABLE). Perbedaan yang disengaja:
--   - FOREIGN KEY ke table `cabang` & `supplier` tidak dibawa (table tsb tidak ada di seed).
--     Kolom & index-nya tetap ada, tambahkan constraint bila table tsb dibuat.
--   - Charset utf8mb4 (sistem asal: latin1) supaya aman untuk teks non-latin.
-- Kompatibel MySQL 5.7 & 8.x
-- =====================================================================

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(50) NOT NULL DEFAULT '-',
  `user_passwd` varchar(50) DEFAULT NULL,
  `user_passwd_sha` varchar(255) DEFAULT NULL COMMENT 'password digunakan untuk backend python',
  `user_karyawan` int(11) NOT NULL DEFAULT '0',
  `user_supplier_id` int(11) DEFAULT NULL COMMENT 'utk hak akses supplier, sementara digunakan di SB',
  `user_log` datetime DEFAULT NULL COMMENT 'value diupdate saat login\r\n- digunakan untuk rentang awal API token login ',
  `user_log_end` datetime DEFAULT NULL COMMENT 'value diupdate saat login +24 jam dari user_log\r\n- digunakan untuk rentang akhir API token login ',
  `user_groups` int(11) DEFAULT NULL,
  `user_kode` varchar(2) DEFAULT NULL,
  `user_keterangan` varchar(250) DEFAULT NULL,
  `user_aktif` enum('Aktif','Tidak Aktif') NOT NULL DEFAULT 'Aktif',
  `user_cabang` varchar(70) NOT NULL DEFAULT '1000000000000000000000000000000000000000000000000000000000000000000000',
  `user_cabang_default` int(11) DEFAULT NULL,
  `fcm_token` text COMMENT 'Digunakan untuk fcm_token aplikasi personalia > nanti akan di sambungkan dengan config.fcm-authorization',
  `fcm_token_excelsa` text COMMENT 'Fungsinya hampir sama dengan kolom fcm_token\r\n\r\nField ini digunakan menyimpan fcm_token aplikasi excelsa, nanti akan di sambungkan dengan config.fcm-authorization-2',
  `api_token` varchar(100) DEFAULT NULL,
  `user_secret_otp` varchar(100) DEFAULT NULL COMMENT 'Digunakan untuk verifikasi OTP Google auth',
  `user_aktif_2fa` enum('Aktif','Tidak Aktif') DEFAULT NULL COMMENT 'Digunakan flag untuk disable/enable fitur 2fa',
  `user_device_id` varchar(100) DEFAULT NULL COMMENT 'user_device_id digunakan pengecekan device aplikasi personalia',
  `user_otp_code` varchar(6) DEFAULT NULL COMMENT 'OTP Digunakan ketika \r\n- reset password (untuk saat ini 01-08-2023)',
  `user_login_status` enum('Y','N') DEFAULT 'N',
  `user_updated_at` datetime DEFAULT NULL,
  `user_updated_by` varchar(50) DEFAULT NULL,
  `user_created_at` datetime DEFAULT NULL,
  `user_created_by` varchar(50) DEFAULT NULL,
  `revised` tinyint(4) DEFAULT NULL,
  `user_deleted_at` datetime DEFAULT NULL,
  `user_deleted_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_kode` (`user_kode`),
  KEY `user_karyawan` (`user_karyawan`),
  KEY `user_name` (`user_name`),
  KEY `FK_users_cabang` (`user_cabang_default`),
  KEY `user_groups` (`user_groups`),
  KEY `user_secret_otp` (`user_secret_otp`),
  KEY `FK_users_supplier` (`user_supplier_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Akun admin awal. Password: Admin@12345  ->  WAJIB diganti setelah login pertama
-- (PATCH /sistem/users/{user_id} dengan body {"password": "..."})
INSERT INTO `users`
    (`user_name`, `user_passwd_sha`, `user_kode`, `user_keterangan`, `user_aktif`, `user_karyawan`,
     `user_groups`, `user_login_status`, `revised`, `user_created_at`, `user_created_by`)
SELECT 'admin', '$pbkdf2-sha256$29000$3BvD2Ns7p9R6D0HIOcfYuw$IiInMlfs6/huUazGV2S6oYD/PTehCEdyRN1L41ggBJc', '01', 'Administrator', 'Aktif', 0,
       1, 'N', 0, NOW(), 'system'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `users` WHERE `user_name` = 'admin');
