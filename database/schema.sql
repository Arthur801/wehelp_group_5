CREATE DATABASE IF NOT EXISTS air_quality
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE air_quality;

CREATE TABLE IF NOT EXISTS air_quality_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    siteid INT NOT NULL,
    sitename VARCHAR(50) NOT NULL,
    county VARCHAR(50),
    aqi INT,
    pollutant VARCHAR(100),
    status VARCHAR(50),
    so2 DECIMAL(10,2),
    co DECIMAL(10,2),
    o3 DECIMAL(10,2),
    o3_8hr DECIMAL(10,2),
    pm10 DECIMAL(10,2),
    pm25 DECIMAL(10,2),
    no2 DECIMAL(10,2),
    nox DECIMAL(10,2),
    no DECIMAL(10,2),
    wind_speed DECIMAL(10,2),
    wind_direc DECIMAL(10,2),
    publishtime DATETIME NOT NULL,
    co_8hr DECIMAL(10,2),
    pm25_avg DECIMAL(10,2),
    pm10_avg DECIMAL(10,2),
    so2_avg DECIMAL(10,2),
    longitude DECIMAL(10,6),
    latitude DECIMAL(10,6),

    UNIQUE KEY unique_site_time (siteid, publishtime)
);