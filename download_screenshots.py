import boto3
import os
from botocore.exceptions import ClientError

# AWS config
AWS_ACCESS_KEY_ID = "AKIARSU6EUUWMQ5I2JWC"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "eu-north-1"
BUCKET_NAME = "ddsfocustime"
S3_BASE_PREFIX = "screenshots/"

# Local base folder where images will be saved
LOCAL_BASE_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "dashboard", "static", "screenshots"
)


# Initialize S3 client
s3 = boto3.client("s3",
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_REGION)


def download_all_screenshots():
    print("🔍 Scanning S3 bucket for screenshots...\n")

    try:
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=S3_BASE_PREFIX)

        downloaded = 0
        skipped = 0

        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]

                if not key.lower().endswith(".png"):
                    continue

                # Relative path under screenshots/
                relative_path = key[len(S3_BASE_PREFIX):]
                local_path = os.path.join(LOCAL_BASE_FOLDER, relative_path)

                # Ensure local folder exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                # Check if the file already exists
                if os.path.exists(local_path):
                    local_mtime = os.path.getmtime(local_path)
                    s3_mtime = obj["LastModified"].timestamp()

                    # If timestamps are basically equal (less than 1 second difference), skip
                    if abs(s3_mtime - local_mtime) < 1:
                        skipped += 1
                        continue

                # Download and save the file
                s3.download_file(BUCKET_NAME, key, local_path)
                os.utime(local_path, (obj["LastModified"].timestamp(), obj["LastModified"].timestamp()))
                downloaded += 1
                print(f"✅ Downloaded: {relative_path}")

        print(f"\n🎉 Finished! {downloaded} new/updated screenshots downloaded.")
        print(f"⏭️ {skipped} images skipped (already up-to-date).")

        # (Optional) Cleanup unused local files — Uncomment carefully:
        # cleanup_unused_local_files(LOCAL_BASE_FOLDER, s3_keys)

    except ClientError as e:
        print(f"[❌] AWS Error: {e}")

# Optional: Clean up local images not present in S3
# def cleanup_unused_local_files(base_folder, s3_keys_set):
#     print("\n🧹 Cleaning up local files not in S3...")
#     for root, _, files in os.walk(base_folder):
#         for f in files:
#             if not f.lower().endswith(".png"):
#                 continue
#             full_path = os.path.join(root, f)
#             rel_path = os.path.relpath(full_path, base_folder).replace("\\", "/")
#             if rel_path not in s3_keys_set:
#                 os.remove(full_path)
#                 print(f"🗑️ Deleted: {rel_path}")

if __name__ == "__main__":
    download_all_screenshots()