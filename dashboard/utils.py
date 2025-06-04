import requests
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor
import time
import boto3
import os
from urllib.parse import quote
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def is_unix_timestamp(value):
    try:
        value_int = int(value)
        return value_int > 946684800
    except:
        return False

def parse_clock_time_string(ts_str):
    try:
        now_date = date.today().strftime("%Y-%m-%d")
        combined = f"{now_date} {ts_str}"
        return datetime.strptime(combined, "%Y-%m-%d %H:%M:%S")
    except:
        return None

def get_all_screenshot_paths():
    base_path = os.path.join(BASE_DIR, 'dashboard', 'media', 'screenshots')
    screenshot_map = {}

    if not os.path.exists(base_path):
        return screenshot_map

    for email in os.listdir(base_path):
        email_path = os.path.join(base_path, email)
        if not os.path.isdir(email_path):
            continue

        for task in os.listdir(email_path):
            task_path = os.path.join(email_path, task)
            if not os.path.isdir(task_path):
                continue

            image_files = [f for f in os.listdir(task_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                path = (
                    "media/screenshots/" +
                    quote(email) + "/" +
                    quote(task) + "/" +
                    quote(image_files[0])
                )
<<<<<<< HEAD
                print(f"[🖼️] Screenshot mapped → Email: {email} | Task: {task} | URL: GET {path}")
=======
                # print(f"[🖼️] Screenshot mapped → Email: {email} | Task: {task} | URL: GET {path}")
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
                screenshot_map[(email.lower(), task.lower())] = path

    return screenshot_map

def fetch_staff_data(offset=0, limit=8, search_query="", days_filter=""):
    TIMESHEET_API = "https://crm.deluxebilisim.com/api/timesheets/"
    TASK_API = "https://crm.deluxebilisim.com/api/tasks/search/"
    PROJECT_API = "https://crm.deluxebilisim.com/api/projects/search/"
    STAFF_API = "https://crm.deluxebilisim.com/api/staffs/"
    HEADERS = {
        'authtoken': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGVsdXhldGltZSIsIm5hbWUiOiJkZWx1eGV0aW1lIiwiQVBJX1RJTUUiOjE3NDUzNDQyNjJ9.kJGo5DksaPwkHwufDvLMGaMmjk5q2F7GhjzwdHtfT_o'
    }

    screenshots_lookup = get_all_screenshot_paths()

    def safe_request(url):
        for attempt in range(3):
            try:
                res = requests.get(url, headers=HEADERS, timeout=5)
                res.raise_for_status()
                return res.json()
            except Exception as e:
                print(f"[Retry {attempt+1}] Error fetching {url}: {e}")
                time.sleep(0.3)
        return {}

    try:
        res = requests.get(TIMESHEET_API, headers=HEADERS, timeout=10)
        res.raise_for_status()
        all_timesheets = res.json()

        if days_filter:
            try:
                days_int = int(days_filter)
                cutoff = datetime.now() - timedelta(days=days_int)
                all_timesheets = [item for item in all_timesheets if is_unix_timestamp(item.get("start_time", 0)) and datetime.fromtimestamp(int(item.get("start_time"))) >= cutoff]
            except ValueError:
                pass

        if search_query:
            filtered = []
            for item in all_timesheets:
                staff_id = item.get("staff_id")
                staff_data = safe_request(f"{STAFF_API}{staff_id}")
                email = staff_data.get("email", "").lower()
                firstname = staff_data.get("firstname", "").lower()
                lastname = staff_data.get("lastname", "").lower()
                fullname = f"{firstname} {lastname}".strip()
                if search_query in email or search_query in firstname or search_query in lastname or search_query in fullname or search_query in str(staff_id):
                    item["_staff_cache"] = staff_data
                    filtered.append(item)
            timesheets = filtered
        else:
            timesheets = all_timesheets

        total_count = len(timesheets)
        timesheets = timesheets[offset:offset + limit]

        def fetch_details(item):
            result = {
                "username": "N/A",
                "job_position": "N/A",
                "last_login": "N/A",
                "task_name": "N/A",
                "project_name": "N/A",
                "total_spent_time": 0,
                "profile_image_url": "https://crm.deluxebilisim.com/assets/images/user_placeholder.jpg",
                "staffid": item.get("staff_id"),
                "email": "",
                "last_update_ago": "Unknown",
                "last_update_full": "Not available",
                "screenshot_url": ""
            }
            try:
                task_id = item.get("task_id")
                project_id = item.get("project_id")
                staff_id = item.get("staff_id")
                start_time_str = item.get("start_time")
                end_time_str = item.get("end_time")

                if task_id:
                    task_data = safe_request(f"{TASK_API}{task_id}")
                    result['task_name'] = task_data[0].get("name", "N/A") if isinstance(task_data, list) else task_data.get("name", "N/A")

                if project_id:
                    project_data = safe_request(f"{PROJECT_API}{project_id}")
                    result['project_name'] = project_data[0].get("name", "N/A") if isinstance(project_data, list) else project_data.get("name", "N/A")

                if staff_id:
                    staff_data = item.get("_staff_cache") or safe_request(f"{STAFF_API}{staff_id}")
                    first = staff_data.get('firstname', '')
                    last = staff_data.get('lastname', '')
                    result['username'] = f"{first} {last}".strip()
                    result['job_position'] = staff_data.get("job_position", "N/A")
                    result['last_login'] = staff_data.get("last_login", "N/A")
                    result['email'] = staff_data.get("email", '')
                    profile_image = staff_data.get("profile_image", "")
                    if profile_image:
                        result['profile_image_url'] = f"https://crm.deluxebilisim.com/uploads/staff_profile_images/{staff_id}/small_{profile_image}"

                start_dt = None
                end_dt = None
                if start_time_str:
                    start_dt = datetime.fromtimestamp(int(start_time_str)) if is_unix_timestamp(start_time_str) else parse_clock_time_string(start_time_str)
                if end_time_str:
                    end_dt = datetime.fromtimestamp(int(end_time_str)) if is_unix_timestamp(end_time_str) else parse_clock_time_string(end_time_str)

                if start_dt and end_dt:
                    result['total_spent_time'] = round((end_dt - start_dt).total_seconds() / 60, 2)
                if end_dt:
                    result['last_update_ago'] = time_ago_from_timestamp(end_dt.timestamp())
                    result['last_update_full'] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                elif start_dt:
                    result['last_update_ago'] = time_ago_from_timestamp(start_dt.timestamp())
                    result['last_update_full'] = start_dt.strftime("%Y-%m-%d %H:%M:%S")

                for (email_key, task_key), path in screenshots_lookup.items():
                    if email_key.startswith(result['email'].split('@')[0]) and task_key == result['task_name'].lower():
<<<<<<< HEAD
                        print(f"[🖼️] Screenshot mapped → Email: {result['email']} | Task: {result['task_name']} | Path: {path}")
=======
                        # print(f"[🖼️] Screenshot mapped → Email: {result['email']} | Task: {result['task_name']} | Path: {path}")
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
                        result['screenshot_url'] = path
                        break

            except Exception as e:
                print(f"[❌] Error fetching details: {e}")

            return result

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(fetch_details, timesheets))

        return {"items": results, "total": total_count}

    except requests.RequestException as e:
        print(f"[❌] API Request Error: {e}")
        return {"items": [], "total": 0}

def time_ago_from_timestamp(ts):
    try:
        ts_float = float(ts)
        now = datetime.now()
        past = datetime.fromtimestamp(ts_float)
        diff = now - past
        total_minutes = int(diff.total_seconds() / 60)

        if total_minutes < 1:
            return "Just now"
        elif total_minutes < 60:
            return f"{total_minutes} minute{'s' if total_minutes != 1 else ''} ago"
        elif total_minutes < 1440:
            hours = total_minutes // 60
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif total_minutes < 10080:
            days = total_minutes // 1440
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif total_minutes < 43200:
            weeks = total_minutes // 10080
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return past.strftime("%d %b %Y at %H:%M")
    except Exception as e:
        print(f"[❌] time_ago_from_timestamp error: {e}")
        return "Unknown"


























def fetch_all_employees():
    API_URL = "https://crm.deluxebilisim.com/api/staffs/"
    HEADERS = {
        'authtoken': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGVsdXhldGltZSIsIm5hbWUiOiJkZWx1eGV0aW1lIiwiQVBJX1RJTUUiOjE3NDUzNDQyNjJ9.kJGo5DksaPwkHwufDvLMGaMmjk5q2F7GhjzwdHtfT_o'
    }

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        staff_list = response.json()

        employees = []
        for staff in staff_list:
            first = staff.get("firstname") or ""
            last = staff.get("lastname") or ""
            position = staff.get("job_position") or ""
            full_name = f"{first.strip()} {last.strip()}"

            if full_name.strip():
                label = f"{full_name} – {position}" if position else full_name
                employees.append(label)

        return employees

    except Exception as e:
        print(f"[❌ fetch_all_employees] Error: {e}")
        return []

