USE retail_shelf_analytics;

-- Clear old lookup listings to avoid primary key constraints
TRUNCATE TABLE product_master_lookup;

-- Seed the new granular product SKU matrix
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
        'Classic Salted (Yellow)',
        'Snacks',
        'Potato Chips'
    ),
    (
        3,
        'Lay\'s',
        'American Style Cream & Onion (Green)',
        'Snacks',
        'Potato Chips'
    ),
    (
        4,
        'Lay\'s',
        'Spanish Tomato Tango (Red)',
        'Snacks',
        'Potato Chips'
    ),
    (
        5,
        'Pringles',
        'Pringles Sour Cream & Onion',
        'Snacks',
        'Potato Chips'
    ),
    (
        6,
        'Pringles',
        'Pringles Original',
        'Snacks',
        'Potato Chips'
    ),
    (
        7,
        'Amul',
        'Pure Milk 1L',
        'Dairy',
        'Fresh Milk'
    ),
    (
        8,
        'Britannia',
        'Good Day Cookies',
        'Snacks',
        'Biscuits'
    ),
    (
        9,
        'Jev',
        'Jev AI Smart Token',
        'Packaged Goods',
        'AI Assets'
    );