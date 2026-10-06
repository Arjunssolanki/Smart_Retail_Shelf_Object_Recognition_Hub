CREATE DATABASE IF NOT EXISTS retail_shelf_analytics;

USE retail_shelf_analytics;

DROP TABLE IF EXISTS bronze_shelf_detections;

DROP TABLE IF EXISTS product_master_lookup;

CREATE TABLE product_master_lookup (
    class_id INT PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL
);

CREATE TABLE bronze_shelf_detections (
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

INSERT INTO
    product_master_lookup (
        class_id,
        brand_name,
        product_name,
        category,
        sub_category
    )
VALUES (
        0,
        'Coca-Cola',
        'Classic Coke 300ml',
        'Beverages',
        'Soft Drinks'
    ),
    (
        1,
        'Pepsi',
        'Pepsi Regular 300ml',
        'Beverages',
        'Soft Drinks'
    ),
    (
        2,
        'Lay\'s',
        'Classic Salted Chips',
        'Snacks',
        'Potato Chips'
    ),
    (
        3,
        'Nestle',
        'Maggi Noodles 70g',
        'Packaged Goods',
        'Instant Noodles'
    ),
    (
        4,
        'Britannia',
        'Good Day Biscuits',
        'Snacks',
        'Biscuits'
    ),
    (
        5,
        'Amul',
        'Pure Milk 1L',
        'Dairy',
        'Fresh Milk'
    ),
    (
        6,
        'Haldiram\'s',
        'Bhujia Sev 150g',
        'Snacks',
        'Traditional Namkeen'
    ),
    (
        7,
        'Tata',
        'Tata Salt 1kg',
        'Packaged Goods',
        'Pantry Staples'
    ),
    (
        8,
        'Jev',
        'Jev AI Smart Token',
        'Packaged Goods',
        'AI Assets'
    );