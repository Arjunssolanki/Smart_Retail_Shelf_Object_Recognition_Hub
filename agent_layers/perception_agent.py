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

    def get_latest_image_key(self):
        response = self.s3.list_objects_v2(Bucket=self.bucket)
        if "Contents" not in response:
            return None
        sorted_objects = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)
        for obj in sorted_objects:
            if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png")):
                return obj["Key"]
        return None

    def fetch_and_encode_image(self, key):
        image_object = self.s3.get_object(Bucket=self.bucket, Key=key)
        return base64.b64encode(image_object["Body"].read()).decode("utf-8")

    def run_vision_inference(self, base64_image):
        prompt = """
        Analyze this retail shelf image. Identify all items from these classes: 
        0: Coca-Cola, 1: Pepsi, 2: Lay's, 3: Nestle, 4: Britannia, 5: Amul, 6: Haldiram's, 7: Tata, 8: Jev.
        For every detected item, return a clean valid JSON array of objects containing exactly:
        "class_id", "confidence", "x_center", "y_center", "width", "height". 
        Output only the raw JSON array inside brackets, no markdown wrappers, no explanation text.
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
            model="llama-3.2-11b-vision-preview",
            temperature=0.0
        )
        return chat_completion.choices.message.content.strip()
