-- =====================================================================
-- Seed FastFlow: buat database (opsional, lewati bila database sudah ada)
-- Nama database disesuaikan dengan DB_CONNECTION_URL di fastflow_api/core/.env
-- Kompatibel MySQL 5.7 & 8.x
-- =====================================================================
CREATE DATABASE IF NOT EXISTS `fastflow_db`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
