import os
from pathlib import Path
from urllib.parse import quote
import openai
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_BASE = os.path.join(BASE_DIR, 'media', 'screenshots')

def normalize_task_name_with_ai(task_name: str) -> str:
    prompt = (
        f"Convert this task name into a folder-safe version by:\n"
        f"- Replacing spaces with underscores (_)"
        f"- Keeping all Turkish characters (ç, ğ, ı, ö, ş, ü)\n"
        f"- Keeping ampersands (&)\n"
        f"- Removing unsafe characters like slashes (/), quotes, colons, etc.\n"
        f"Task name: {task_name}\n"
        f"Folder-safe version:"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a string normalizer."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[❌ AI Normalization Failed]: {e}")
        fallback = task_name.replace(" ", "_")
        fallback = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ&]', '', fallback)
        return fallback

def get_latest_screenshot_paths() -> dict:
    """
    Scans the entire screenshot folder tree and returns a dictionary:
    { (email.lower(), normalized_task_name.lower()): "/media/screenshots/...image.png" }
    """
    screenshot_map = {}
    if not os.path.exists(SCREENSHOT_BASE):
        return screenshot_map

    for email in os.listdir(SCREENSHOT_BASE):
        email_path = os.path.join(SCREENSHOT_BASE, email)
        if not os.path.isdir(email_path):
            continue

        for task in os.listdir(email_path):
            task_path = os.path.join(email_path, task)
            if not os.path.isdir(task_path):
                continue

            image_files = [f for f in os.listdir(task_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                latest_image = sorted(
                    image_files,
                    key=lambda f: os.path.getmtime(os.path.join(task_path, f)),
                    reverse=True
                )[0]

                normalized_task = normalize_task_name_with_ai(task)
                key = (email.lower(), normalized_task.lower())

                url = f"/media/screenshots/{quote(email)}/{quote(normalized_task)}/{quote(latest_image)}"
                screenshot_map[key] = url

                print(f"[📦 Mapped] {key} → {url}")

    return screenshot_map
