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
        Analyze this retail shelf image. You must differentiate between different product items within the same category by looking closely at text logos, product names, packaging designs, and distinct wrapper colors.
        
        Classify each item based on these explicit product rules:
        - 0: Coca-Cola (Red cans/bottles with white script logotype)
        - 1: Pepsi (Blue cans/bottles with globe logo)
        - 2: Lay's Classic Salted (Bright Yellow potato chip bags)
        - 3: Lay's American Style Cream & Onion (Bright Green potato chip bags)
        - 4: Lay's Spanish Tomato Tango (Deep Red potato chip bags)
        - 5: Pringles Sour Cream & Onion (Green cylindrical Pringles tube cans)
        - 6: Pringles Original (Red cylindrical Pringles tube cans)
        - 7: Amul Pure Milk (White and blue dairy milk packets)
        - 8: Britannia Good Day (Round cookie/biscuit packs)
        - 9: Jev AI Assets (AI items/tokens)
        
        For every single product item detected on the shelves, return a clean valid JSON array of objects containing exactly:
        "class_id", "confidence", "x_center", "y_center", "width", "height".
        
        CRITICAL: Inspect every individual row and column shelf facet item by item. Do not bundle different flavored chip bags under the same class_id. Output only the raw JSON array inside brackets, no markdown wrappers, no conversational text.
        """
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.0,
            max_tokens=800  # Explicitly safely anchor limits to bypass the 1000 OTPM ceiling
        )
        return chat_completion.choices[0].message.content.strip()
