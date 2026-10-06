import os
import mysql.connector
import pandas as pd
import streamlit as st
import warnings
from dotenv import load_dotenv
from groq import Groq

warnings.filterwarnings("ignore", category=UserWarning)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def run_sql_agent(user_query):
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    schema_context = """
    You are a professional MySQL database assistant. Given the user's natural language question, write a single valid MySQL query to answer it.
    The database name is 'retail_shelf_analytics' and has these tables:
    1. bronze_shelf_detections (detection_id, scan_timestamp, store_id, client_number, image_filename, detected_brand, detected_product, confidence_score, x_center, y_center, bbox_width, bbox_height)
    2. silver_shelf_inventory (inventory_id, detection_id, scan_timestamp, store_id, client_number, image_filename, brand_name, product_name, confidence_score, x_center, y_center, bbox_width, bbox_height)
    3. dim_products (product_key, brand_name, product_name)
    4. dim_stores (store_key, store_id, client_number)
    5. dim_calendar (date_key, full_date, day_of_week, month_name, quarter, year_val)
    6. fact_shelf_compliance (fact_id, date_key, store_key, product_key, image_filename, total_detected_count, average_confidence, occupied_surface_area)
    
    Output ONLY the raw executable SQL query string, no explanation text, no markdown code blocks.
    """
    completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": schema_context},
            {"role": "user", "content": user_query}
        ],
        model="qwen/qwen3.8-27b",
        temperature=0.0
    )
    sql_query = completion.choices[0].message.content.strip()
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql_query:
        sql_query = sql_query.split("```")[1].strip()
    return sql_query

def main():
    load_dotenv()
    st.set_page_config(page_title="Smart Retail Shelf Recognition Hub", page_icon="📊", layout="wide")
    
    st.title("📊 Smart Retail Shelf Recognition Hub")
    st.markdown("### Real-Time Multi-Agent Share-of-Shelf (SoS) Analytics")
    
    if st.button("🔄 Clear App Cache & Refresh Dashboard"):
        st.cache_data.clear()
        st.rerun()
        
    st.write("---")
    
    # --- SECTION 1: AI SQL AGENT ---
    st.subheader("🤖 GenAI Copilot: Query the Database via Chat")
    user_input = st.text_input("Ask a question about the shelf inventory:")
    
    if user_input:
        with st.spinner("Agent translating to SQL..."):
            generated_sql = run_sql_agent(user_input)
            st.code(generated_sql, language="sql")
            try:
                conn = get_db_connection()
                result_df = pd.read_sql(generated_sql, conn)
                conn.close()
                st.success("✅ Query executed successfully!")
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Execution failed: {str(e)}")
                
    st.write("---")
    
    # --- SECTION 2: ANALYTICS CORE ---
    try:
        conn = get_db_connection()
    except Exception:
        st.error("❌ Unable to establish connection to local MySQL server.")
        return
        
    query_metrics = """
        SELECT 
            p.brand_name,
            p.product_name,
            SUM(f.total_detected_count) as total_items,
            AVG(f.average_confidence) as avg_conf,
            SUM(f.occupied_surface_area) as total_area
        FROM fact_shelf_compliance f
        JOIN dim_products p ON f.product_key = p.product_key
        GROUP BY p.brand_name, p.product_name
    """
    df = pd.read_sql(query_metrics, conn)
    conn.close()
    
    if df.empty:
        st.warning("⚠️ Gold analytical warehouse tables are currently empty.")
        return
        
    total_shelf_items = int(df["total_items"].sum())
    avg_pipeline_confidence = float(df["avg_conf"].mean())
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Total Shelf Items Tracked", value=f"{total_shelf_items:,}")
    with m2:
        st.metric(label="Average Perception Accuracy", value=f"{avg_pipeline_confidence:.2%}")
    with m3:
        st.metric(label="Active Brand Varieties Found", value=len(df["brand_name"].unique()))
        
    st.write("---")
    
    df["Share of Shelf (%)"] = (df["total_items"] / total_shelf_items) * 100
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📦 Brand Share-of-Shelf (SoS) Distribution")
        st.bar_chart(data=df, x="brand_name", y="Share of Shelf (%)", use_container_width=True)
    with c2:
        st.subheader("📁 Product Variety Breakdown Analysis")
        st.bar_chart(data=df, x="product_name", y="total_items", use_container_width=True)
        
    st.write("---")
    st.subheader("📋 Granular Operational Inventory Logs")
    st.dataframe(
        df[["brand_name", "product_name", "total_items", "Share of Shelf (%)"]].sort_values(by="total_items", ascending=False),
        use_container_width=True, hide_index=True
    )

if __name__ == "__main__":
    main()
