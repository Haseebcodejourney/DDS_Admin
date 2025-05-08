import boto3
from botocore.exceptions import ClientError
import re
import unicodedata

def clean_for_s3(name):
    # Normalize Turkish characters and remove unsafe symbols
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = name.replace(" ", "").replace(".", "").lower()
    return re.sub(r"[^a-z0-9]", "", name)

def get_latest_screenshot_url(email, task_name):
    s3 = boto3.client("s3",
                      aws_access_key_id="AKIARSU6EUUWMQ5I2JWC",
                      aws_secret_access_key="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",
                      region_name="us-east-1")

    base_prefix = f"screenshots/{email}/"
    try:
        # Step 1: list all folders under this user
        response = s3.list_objects_v2(Bucket="ddsfocustime", Prefix=base_prefix, Delimiter="/")
        all_objects = s3.list_objects_v2(Bucket="ddsfocustime", Prefix=base_prefix)

        # Step 2: Try to match folder with task name
        task_key = clean_for_s3(task_name)

        matches = []
        for obj in all_objects.get("Contents", []):
            parts = obj["Key"].split("/")
            if len(parts) >= 3:
                folder = parts[2]
                if clean_for_s3(folder) == task_key:
                    matches.append(obj)

        if not matches:
            print(f"[❌] No match for task: {task_name}")
            return None

        # Step 3: Return the latest screenshot
        matches.sort(key=lambda x: x["LastModified"], reverse=True)
        latest_key = matches[0]["Key"]
        url = f"https://ddsfocustime.s3.amazonaws.com/{latest_key}"
        print(f"[🖼️] Matched Screenshot URL: {url}")
        return url

    except ClientError as e:
        print(f"[❌] S3 Access Error: {e}")
        return None
