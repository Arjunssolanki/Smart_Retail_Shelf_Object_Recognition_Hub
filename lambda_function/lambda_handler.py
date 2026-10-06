import os
import json
import base64
import urllib.parse
import boto3
import mysql.connector
from groq import Groq

# Initialize the core AWS S3 SDK infrastructure hook
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    # Parse incoming event drop parameters from the active S3 trigger stream
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    
    try:
        # Fetch raw image file payload array bytes out of your target S3 bucket channel
        image_object = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = image_object["Body"].read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        return {"statusCode": 500, "body": f"S3 Ingestion Stream Fetch failed: {str(e)}"}
        
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Dynamic Open-Vocabulary extraction prompt blueprint
    prompt = """
    Analyze this retail shelf image. Your job is to locate and count EVERY SINGLE individual product item displayed on the shelves. Do not skip any item.

    For every single product pack, box, bag, or bottle detected, you must return a valid JSON array of objects containing exactly:
    - "detected_brand": The explicit brand name printed on the item (e.g., 'Lay's', 'Oreo', 'Doritos'). If completely unreadable, use 'Generic'.
    - "detected_product": The granular product variant or flavor (e.g., 'Classic Salted', 'Chocolate Cream'). If unknown, use 'Other'.
    - "confidence": A prediction value between 0.0 and 1.0.
    - "x_center": Bounding box X center coordinate.
    - "y_center": Bounding box Y center coordinate.
    - "width": Bounding box width.
    - "height": Bounding box height.

    CRITICAL: Inspect every individual shelf facet row by row. Do not bundle group items together. Return ONLY the raw JSON array inside brackets, no markdown code wrappers, no explanation text.
    """
    
    try:
        # Route visual frames to the Groq Cloud endpoints
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.0
        )
        
        raw_response = chat_completion.choices[0].message.content.strip()
        
        # Safe extraction check to bypass text generation noise
        if "[" in raw_response and "]" in raw_response:
            start = raw_response.find("[")
            end = raw_response.rfind("]") + 1
            detections = json.loads(raw_response[start:end])
        else:
            detections = json.loads(raw_response)
    except Exception as e:
        return {"statusCode": 500, "body": f"Vision AI Multi-Agent Inference failed: {str(e)}"}
        
    try:
        # Establish connection pool links to the database host instance environment
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO bronze_shelf_detections (
                store_id, client_number, image_filename, detected_brand, detected_product, confidence_score,
                x_center, y_center, bbox_width, bbox_height
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Load entries into the operational transactional layers
        for item in detections:
            cursor.execute(insert_query, (
                "STORE_MOCK_99",
                "CLI_MOCK_88",
                key,
                str(item["detected_brand"]),
                str(item["detected_product"]),
                float(item["confidence"]),
                float(item["x_center"]),
                float(item["y_center"]),
                float(item["width"]),
                float(item["height"])
            ))
            
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return {"statusCode": 500, "body": f"Warehouse Database Ingestion failed: {str(e)}"}
        
    return {"statusCode": 200, "body": json.dumps("Detections successfully logged to MySQL")}
