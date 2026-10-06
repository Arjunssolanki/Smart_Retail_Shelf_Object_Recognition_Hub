import os
import mysql.connector
import pandas as pd
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)

def calculate_iou(boxA, boxB):
    """
    Calculates Intersection over Union (IoU) between two bounding boxes.
    Boxes are in format: [x1, y1, x2, y2]
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
        
    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea <= 0:
        return 0.0
        
    return interArea / unionArea

def apply_nms(df, iou_threshold=0.5):
    """
    Applies Non-Maximum Suppression (NMS) per image subset.
    """
    if df.empty:
        return df
        
    df = df.sort_values(by="confidence_score", ascending=False).reset_index(drop=True)
    keep_indices = []
    boxes = []
    
    for _, row in df.iterrows():
        x, y, w, h = row["x_center"], row["y_center"], row["bbox_width"], row["bbox_height"]
        x1 = float(x) - (float(w) / 2.0)
        y1 = float(y) - (float(h) / 2.0)
        x2 = float(x) + (float(w) / 2.0)
        y2 = float(y) + (float(h) / 2.0)
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

    try:
        # 1. Fetch active image filenames from bronze table
        cursor.execute("SELECT DISTINCT image_filename FROM bronze_shelf_detections")
        active_files = [r[0] for r in cursor.fetchall()]
        
        if not active_files:
            print("No active image records found in bronze_shelf_detections.")
            return

        # 2. Idempotent cleanup: Remove existing silver records for active files before re-inserting
        format_strings = ', '.join(['%s'] * len(active_files))
        delete_query = f"DELETE FROM silver_shelf_inventory WHERE image_filename IN ({format_strings})"
        cursor.execute(delete_query, tuple(active_files))

        # 3. Read bronze records into DataFrame
        raw_query = "SELECT * FROM bronze_shelf_detections"
        df_bronze = pd.read_sql(raw_query, conn)
        
        if df_bronze.empty:
            return
            
        # 4. Filter by confidence score threshold
        df_clean = df_bronze[df_bronze["confidence_score"] >= 0.65].copy()
        
        # 5. Apply NMS per image group
        final_filtered_list = []
        for img in df_clean["image_filename"].unique():
            df_img_subset = df_clean[df_clean["image_filename"] == img].copy()
            df_img_filtered = apply_nms(df_img_subset)
            final_filtered_list.append(df_img_filtered)
            
        if final_filtered_list:
            df_filtered = pd.concat(final_filtered_list, ignore_index=True)
        else:
            df_filtered = pd.DataFrame(columns=df_clean.columns)
            
        if df_filtered.empty:
            conn.commit()
            return

        # 6. Align column names with standard bronze schema & prepare bulk insert
        insert_query = """
            INSERT INTO silver_shelf_inventory (
                detection_id, scan_timestamp, store_id, client_number, image_filename,
                brand_name, product_name, confidence_score, x_center, y_center, bbox_width, bbox_height
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Use column fallbacks for brand/product naming compatibility
        brand_col = "detected_brand" if "detected_brand" in df_filtered.columns else "brand_name"
        product_col = "detected_product" if "detected_product" in df_filtered.columns else "product_name"

        records_to_insert = [
            (
                int(row["detection_id"]),
                row["scan_timestamp"],
                row["store_id"],
                row["client_number"],
                row["image_filename"],
                str(row[brand_col]),
                str(row[product_col]),
                float(row["confidence_score"]),
                float(row["x_center"]),
                float(row["y_center"]),
                float(row["bbox_width"]),
                float(row["bbox_height"])
            )
            for _, row in df_filtered.iterrows()
        ]

        # 7. Perform bulk insert via executemany for high performance
        cursor.executemany(insert_query, records_to_insert)
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Silver layer transformation failed: {e}")
        raise e

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    transform_bronze_to_silver()