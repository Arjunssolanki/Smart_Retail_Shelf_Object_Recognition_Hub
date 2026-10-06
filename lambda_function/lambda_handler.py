import os
import json
import base64
import urllib.parse
import boto3
import mysql.connector
from groq import Groq

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    bucket = event["Records"]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"]["s3"]["object"]["key"], encoding="utf-8")
    
    try:
        image_object = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = image_object["Body"].read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
        
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = """
    Analyze this retail shelf image. Identify all items from these classes: 
    0: Coca-Cola, 1: Pepsi, 2: Lay's, 3: Nestle, 4: Britannia, 5: Amul, 6: Haldiram's, 7: Tata, 8: Jev.
    For every detected item, return a clean valid JSON array of objects containing exactly:
    "class_id", "confidence", "x_center", "y_center", "width", "height". 
    Output only the raw JSON array inside brackets, no markdown wrappers, no explanation text.
    """
    
    try:
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
            model="llama-3.2-11b-vision-preview",
            temperature=0.0
        )
        
        raw_response = chat_completion.choices.message.content.strip()
        
        if "[" in raw_response and "]" in raw_response:
            start = raw_response.find("[")
            end = raw_response.rfind("]") + 1
            detections = json.loads(raw_response[start:end])
        else:
            detections = json.loads(raw_response)
    except Exception as e:
        return {"statusCode": 500, "body": f"AI Inference failed: {str(e)}"}
        
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO bronze_shelf_detections (
                store_id, client_number, image_filename, class_id, confidence_score,
                x_center, y_center, bbox_width, bbox_height
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for item in detections:
            cursor.execute(insert_query, (
                "STORE_MOCK_99",
                "CLI_MOCK_88",
                key,
                int(item["class_id"]),
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
        return {"statusCode": 500, "body": f"Database Load failed: {str(e)}"}
        
    return {"statusCode": 200, "body": json.dumps("Detections successfully logged to MySQL")}
