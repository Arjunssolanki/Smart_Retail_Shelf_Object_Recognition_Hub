-- 1. Create the dedicated retail analytics database container
CREATE DATABASE IF NOT EXISTS retail_shelf_analytics;

USE retail_shelf_analytics;

-- 2. Construct the Bronze layer table to log raw, unverified AI metrics
CREATE TABLE IF NOT EXISTS bronze_shelf_detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY,
    scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    store_id VARCHAR(50) NOT NULL,
    client_number VARCHAR(50) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    class_id INT NOT NULL,
    confidence_score DECIMAL(5, 4) NOT NULL,
    x_center DECIMAL(10, 4) NOT NULL,
    y_center DECIMAL(10, 4) NOT NULL,
    bbox_width DECIMAL(10, 4) NOT NULL,
    bbox_height DECIMAL(10, 4) NOT NULL
);