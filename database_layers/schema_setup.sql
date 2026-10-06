CREATE DATABASE IF NOT EXISTS retail_shelf_analytics;

USE retail_shelf_analytics;

DROP TABLE IF EXISTS fact_shelf_compliance;

DROP TABLE IF EXISTS silver_shelf_inventory;

DROP TABLE IF EXISTS bronze_shelf_detections;

DROP TABLE IF EXISTS dim_products;

DROP TABLE IF EXISTS dim_stores;

DROP TABLE IF EXISTS dim_calendar;

-- Raw Unprocessed Visual Inferences Stage
CREATE TABLE bronze_shelf_detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY,
    scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    store_id VARCHAR(50) NOT NULL,
    client_number VARCHAR(50) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    detected_brand VARCHAR(150) NOT NULL,
    detected_product VARCHAR(150) NOT NULL,
    confidence_score DECIMAL(5, 4) NOT NULL,
    x_center DECIMAL(10, 4) NOT NULL,
    y_center DECIMAL(10, 4) NOT NULL,
    bbox_width DECIMAL(10, 4) NOT NULL,
    bbox_height DECIMAL(10, 4) NOT NULL
);

-- Spatial Deduplication NMS Layer Stage
CREATE TABLE silver_shelf_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    detection_id INT NOT NULL,
    scan_timestamp DATETIME NOT NULL,
    store_id VARCHAR(50) NOT NULL,
    client_number VARCHAR(50) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    brand_name VARCHAR(150) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    confidence_score DECIMAL(5, 4) NOT NULL,
    x_center DECIMAL(10, 4) NOT NULL,
    y_center DECIMAL(10, 4) NOT NULL,
    bbox_width DECIMAL(10, 4) NOT NULL,
    bbox_height DECIMAL(10, 4) NOT NULL
);

-- Analytical Star Schema Dimension and Fact Layer
CREATE TABLE dim_products (
    product_key INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(150) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    UNIQUE KEY idx_brand_prod (brand_name, product_name)
);

CREATE TABLE dim_stores (
    store_key INT AUTO_INCREMENT PRIMARY KEY,
    store_id VARCHAR(50) UNIQUE NOT NULL,
    client_number VARCHAR(50) NOT NULL
);

CREATE TABLE dim_calendar (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter INT NOT NULL,
    year_val INT NOT NULL
);

CREATE TABLE fact_shelf_compliance (
    fact_id INT AUTO_INCREMENT PRIMARY KEY,
    date_key INT NOT NULL,
    store_key INT NOT NULL,
    product_key INT NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    total_detected_count INT NOT NULL,
    average_confidence DECIMAL(5, 4) NOT NULL,
    occupied_surface_area DECIMAL(12, 4) NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_calendar (date_key),
    FOREIGN KEY (store_key) REFERENCES dim_stores (store_key),
    FOREIGN KEY (product_key) REFERENCES dim_products (product_key)
);