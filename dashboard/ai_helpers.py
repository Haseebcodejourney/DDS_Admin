import os
from pathlib import Path
from urllib.parse import quote
<<<<<<< HEAD
import openai
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_BASE = os.path.join(BASE_DIR, 'media', 'screenshots')
=======
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# OpenAI setup
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Base paths
BASE_DIR = Path(__file__).resolve().parent  # Adjusted to reflect the 'dashboard' directory
SCREENSHOT_BASE = os.path.join(BASE_DIR, 'media', 'screenshots')  # Corrected path

>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af

def normalize_task_name_with_ai(task_name: str) -> str:
    prompt = (
        f"Convert this task name into a folder-safe version by:\n"
<<<<<<< HEAD
        f"- Replacing spaces with underscores (_)"
=======
        f"- Replacing spaces with underscores (_)\n"
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
        f"- Keeping all Turkish characters (ç, ğ, ı, ö, ş, ü)\n"
        f"- Keeping ampersands (&)\n"
        f"- Removing unsafe characters like slashes (/), quotes, colons, etc.\n"
        f"Task name: {task_name}\n"
        f"Folder-safe version:"
    )

    try:
<<<<<<< HEAD
        response = openai.ChatCompletion.create(
=======
        response = client.chat.completions.create(
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a string normalizer."},
                {"role": "user", "content": prompt}
            ]
        )
<<<<<<< HEAD
        return response['choices'][0]['message']['content'].strip()
=======
        return response.choices[0].message.content.strip()
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
    except Exception as e:
        print(f"[❌ AI Normalization Failed]: {e}")
        fallback = task_name.replace(" ", "_")
        fallback = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ&]', '', fallback)
        return fallback

<<<<<<< HEAD
def get_latest_screenshot_paths() -> dict:
    """
    Scans the entire screenshot folder tree and returns a dictionary:
    { (email.lower(), normalized_task_name.lower()): "/media/screenshots/...image.png" }
    """
    screenshot_map = {}
    if not os.path.exists(SCREENSHOT_BASE):
=======

def generate_screenshot_html(screenshot_map: dict) -> str:
    """
    Generates HTML for displaying screenshots.
    :param screenshot_map: Dictionary of screenshot paths.
    :return: HTML string.
    """
    html = '<div class="screenshot-gallery">\n'
    for (email, task), url in screenshot_map.items():
        html += (
            f'  <div class="screenshot-item">\n'
            f'    <p><strong>Email:</strong> {email}</p>\n'
            f'    <p><strong>Task:</strong> {task}</p>\n'
            f'    <img src="{url}" alt="Screenshot for {task}" />\n'
            f'  </div>\n'
        )
    html += '</div>'
    return html


def get_all_screenshot_paths() -> dict:
    """
    Scans the entire screenshot folder tree and returns a dictionary:
    { (email.lower(), normalized_task_name.lower()): ["/media/screenshots/...image1.png", "/media/screenshots/...image2.png", ...] }
    """
    print("[DEBUG] get_all_screenshot_paths function called.")  # Debug print

    screenshot_map = {}
    if not os.path.exists(SCREENSHOT_BASE):
        print("[⚠️ Warning] Screenshot base directory does not exist.")
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
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
<<<<<<< HEAD
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
=======
                normalized_task = normalize_task_name_with_ai(task)
                key = (email.lower(), normalized_task.lower())

                urls = [
                    f"/media/screenshots/{quote(email)}/{quote(normalized_task)}/{quote(image)}"
                    for image in sorted(
                        image_files,
                        key=lambda f: os.path.getmtime(os.path.join(task_path, f)),
                        reverse=True
                    )
                ]
                screenshot_map[key] = urls

                print(f"[📦 Mapped] {key} → {urls}")  # Debug print
            else:
                print(f"[⚠️ No Images] No images found in {task_path}")  # Debug print

    print("[✅ Screenshot Map Result]:", screenshot_map)  # Debug print for the result
    return screenshot_map

# Example usage:
if __name__ == "__main__":
    print("[DEBUG] Script started.")  # Debug print
    screenshot_map = get_all_screenshot_paths()
    print("[🖼️ Final Screenshot Map]:", screenshot_map)
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
