import os
import base64
import boto3
from groq import Groq

class PerceptionAgent:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.bucket = os.getenv("S3_BUCKET_NAME")
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def get_all_s3_image_keys(self):
        response = self.s3.list_objects_v2(Bucket=self.bucket)
        if "Contents" not in response:
            return []
        
        image_keys = []
        for obj in response["Contents"]:
            if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png")):
                image_keys.append(obj["Key"])
        return image_keys

    def fetch_and_encode_image(self, key):
        image_object = self.s3.get_object(Bucket=self.bucket, Key=key)
        return base64.b64encode(image_object["Body"].read()).decode("utf-8")

    def run_vision_inference(self, base64_image):
        prompt = """
        Return a valid JSON array of objects for every product item detected on the shelves.
        Each object MUST contain exactly:
        - "detected_brand": The brand name (e.g., 'Lay's', 'Oreo'). If unreadable, use 'Generic'.
        - "detected_product": The variant/flavor (e.g., 'Classic Salted'). If unknown, use 'Other'.
        - "confidence": A value between 0.0 and 1.0.
        - "x_center", "y_center", "width", "height": Bounding box coordinates.

        CRITICAL OUTPUT RULE: Do not output any markdown code blocks, do not include any text before or after the JSON, and do not provide an introduction or thinking logs. Output ONLY the raw '[' and ']' array structure.
        """
        
        chat_completion = self.groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=800
        )
        return chat_completion.choices[0].message.content.strip()
