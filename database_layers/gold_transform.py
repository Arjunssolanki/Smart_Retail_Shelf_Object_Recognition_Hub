import os
import mysql.connector
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

def process_silver_to_gold():
    load_dotenv()
    
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    
    current_date = datetime.now().date()
    date_key = int(current_date.strftime("%Y%m%d"))
    
    cursor.execute("SELECT COUNT(*) FROM dim_calendar WHERE date_key = %s", (date_key,))
    if cursor.fetchone()[0] == 0:
        insert_date_query = """
            INSERT INTO dim_calendar (date_key, full_date, day_of_week, month_name, quarter, year_val)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_date_query, (
            date_key,
            current_date,
            current_date.strftime("%A"),
            current_date.strftime("%B"),
            (current_date.month - 1) // 3 + 1,
            current_date.year
        ))
        
    silver_query = """
        SELECT store_id, client_number, image_filename, brand_name, category, confidence_score, bbox_width, bbox_height 
        FROM silver_shelf_inventory
    """
    df_silver = pd.read_sql(silver_query, conn)
    
    if df_silver.empty:
        cursor.close()
        conn.close()
        return
        
    unique_stores = df_silver[["store_id", "client_number"]].drop_duplicates()
    for _, store in unique_stores.iterrows():
        cursor.execute("SELECT store_key FROM dim_stores WHERE store_id = %s", (store["store_id"],))
        store_res = cursor.fetchone()
        if not store_res:
            cursor.execute(
                "INSERT INTO dim_stores (store_id, client_number) VALUES (%s, %s)",
                (store["store_id"], store["client_number"])
            )
            
    df_silver["surface_area"] = df_silver["bbox_width"] * df_silver["bbox_height"]
    
    grouped = df_silver.groupby(["store_id", "brand_name", "category", "image_filename"]).agg(
        total_count=("confidence_score", "count"),
        avg_confidence=("confidence_score", "mean"),
        total_surface_area=("surface_area", "sum")
    ).reset_index()
    
    insert_fact_query = """
        INSERT INTO fact_shelf_compliance (
            date_key, store_key, product_key, image_filename, total_detected_count, average_confidence, occupied_surface_area
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    for _, row in grouped.iterrows():
        cursor.execute("SELECT store_key FROM dim_stores WHERE store_id = %s", (row["store_id"],))
        store_key = cursor.fetchone()[0]
        
        cursor.execute("SELECT product_key FROM dim_products WHERE brand_name = %s AND category = %s", (row["brand_name"], row["category"]))
        prod_res = cursor.fetchone()
        
        if prod_res:
            product_key = prod_res[0]
        else:
            cursor.execute("SELECT product_key FROM dim_products WHERE brand_name = 'Generic'")
            product_key = cursor.fetchone()[0]
            
        cursor.execute(insert_fact_query, (
            date_key,
            store_key,
            product_key,
            row["image_filename"],
            int(row["total_count"]),
            float(row["avg_confidence"]),
            float(row["total_surface_area"])
        ))
        
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    process_silver_to_gold()
