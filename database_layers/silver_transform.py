import os
import mysql.connector
import pandas as pd
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    interArea = max(0, xB - xA) * max(0, yB - yA)
    
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    if float(boxAArea + boxBArea - interArea) <= 0:
        return 0.0
        
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def apply_nms(df, iou_threshold=0.5):
    if df.empty:
        return df
        
    df = df.sort_values(by="confidence_score", ascending=False).reset_index(drop=True)
    keep_indices = []
    
    boxes = []
    for idx, row in df.iterrows():
        x, y, w, h = row["x_center"], row["y_center"], row["bbox_width"], row["bbox_height"]
        x1 = float(x) - (float(w) / 2)
        y1 = float(y) - (float(h) / 2)
        x2 = float(x) + (float(w) / 2)
        y2 = float(y) + (float(h) / 2)
        boxes.append([x1, y1, x2, y2])
        
    for i in range(len(boxes)):
        discard = False
        for j in keep_indices:
            if calculate_iou(boxes[i], boxes[j]) > iou_threshold:
                discard = True
                break
        if not discard:
            keep_indices.append(i)
            
    return df.iloc[keep_indices].reset_index(drop=True)

def transform_bronze_to_silver():
    load_dotenv()
    
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS silver_shelf_inventory (
            inventory_id INT AUTO_INCREMENT PRIMARY KEY,
            detection_id INT,
            scan_timestamp DATETIME,
            store_id VARCHAR(50),
            client_number VARCHAR(50),
            image_filename VARCHAR(255),
            brand_name VARCHAR(100),
            category VARCHAR(100),
            confidence_score DECIMAL(5,4),
            x_center DECIMAL(10,4),
            y_center DECIMAL(10,4),
            bbox_width DECIMAL(10,4),
            bbox_height DECIMAL(10,4)
        )
    """)
    
    cursor.execute("SELECT DISTINCT image_filename FROM bronze_shelf_detections")
    active_files = [r[0] for r in cursor.fetchall()]
    
    for f in active_files:
        cursor.execute("DELETE FROM silver_shelf_inventory WHERE image_filename = %s", (f,))
        
    raw_query = "SELECT * FROM bronze_shelf_detections"
    df_bronze = pd.read_sql(raw_query, conn)
    
    if df_bronze.empty:
        cursor.close()
        conn.close()
        return
        
    df_clean = df_bronze[df_bronze["confidence_score"] >= 0.65].copy()
    
    # Process files sequentially to maintain stability across all pandas versions
    final_filtered_list = []
    unique_images = df_clean["image_filename"].unique()
    
    for img in unique_images:
        df_img_subset = df_clean[df_clean["image_filename"] == img].copy()
        df_img_filtered = apply_nms(df_img_subset)
        final_filtered_list.append(df_img_filtered)
        
    if final_filtered_list:
        df_filtered = pd.concat(final_filtered_list, ignore_index=True)
    else:
        df_filtered = pd.DataFrame(columns=df_clean.columns)
    
    df_lookup = pd.read_sql("SELECT class_id, brand_name, category FROM product_master_lookup", conn)
    
    df_merged = pd.merge(df_filtered, df_lookup, on="class_id", how="left")
    df_merged["brand_name"] = df_merged["brand_name"].fillna("Generic")
    df_merged["category"] = df_merged["category"].fillna("Other")
    
    insert_query = """
        INSERT INTO silver_shelf_inventory (
            detection_id, scan_timestamp, store_id, client_number, image_filename,
            brand_name, category, confidence_score, x_center, y_center, bbox_width, bbox_height
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for _, row in df_merged.iterrows():
        cursor.execute(insert_query, (
            int(row["detection_id"]), row["scan_timestamp"], row["store_id"], row["client_number"],
            row["image_filename"], row["brand_name"], row["category"], float(row["confidence_score"]),
            float(row["x_center"]), float(row["y_center"]), float(row["bbox_width"]), float(row["bbox_height"])
        ))
        
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    transform_bronze_to_silver()
