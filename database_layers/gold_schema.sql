USE retail_shelf_analytics;

DROP TABLE IF EXISTS fact_shelf_compliance;

DROP TABLE IF EXISTS dim_products;

DROP TABLE IF EXISTS dim_stores;

DROP TABLE IF EXISTS dim_calendar;

CREATE TABLE dim_products (
    product_key INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    UNIQUE KEY idx_brand (brand_name, category)
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

INSERT INTO
    dim_products (brand_name, category)
SELECT DISTINCT
    brand_name,
    category
FROM product_master_lookup
ON DUPLICATE KEY UPDATE
    dim_products.brand_name = VALUES(brand_name);

INSERT INTO
    dim_products (brand_name, category)
VALUES ('Generic', 'Other')
ON DUPLICATE KEY UPDATE
    dim_products.brand_name = VALUES(brand_name);