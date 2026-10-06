import os
import mysql.connector
from dotenv import load_dotenv
from agent_layers.perception_agent import PerceptionAgent
from agent_layers.validation_agent import ValidationAgent
from agent_layers.ingestion_agent import IngestionAgent

def run_coordinated_pipeline():
    load_dotenv()
    
    perception = PerceptionAgent()
    validator = ValidationAgent()
    ingestion = IngestionAgent()
    
    all_file_keys = perception.get_all_s3_image_keys()
    if not all_file_keys:
        print("INFO: No images found in S3 bucket.")
        return
        
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    
    for file_key in all_file_keys:
        cursor.execute("SELECT COUNT(*) FROM bronze_shelf_detections WHERE image_filename = %s", (file_key,))
        if cursor.fetchone()[0] > 0:
            print(f"SKIPPING: {file_key} - Already ingested in Bronze layer.")
            continue
            
        print(f"PROCESSING: New S3 image stream identified: {file_key}")
        base64_frame = perception.fetch_and_encode_image(file_key)
        raw_ai_output = perception.run_vision_inference(base64_frame)
        
        raw_json = validator.parse_and_validate_json(raw_ai_output)
        if not raw_json:
            continue
            
        enriched_json = validator.enrich_catalog_with_jev_ai(raw_json)
        clean_records = validator.filter_malformed_records(enriched_json)
        
        if clean_records:
            ingestion.load_to_bronze_layer(file_key, clean_records)
            print(f"SUCCESS: Logged {len(clean_records)} items from {file_key} to Bronze table.")
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_coordinated_pipeline()
