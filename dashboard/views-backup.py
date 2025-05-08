import requests
from django.shortcuts import render
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import os
from urllib.parse import quote
from pathlib import Path

# View for Login Page
def login_view(request):
    return render(request, 'dashboard/login.html')

# View for Dashboard Index Page
def index(request):
    return render(request, 'dashboard/index.html')

# View for Home Page
def home(request):
    return render(request, 'dashboard/home.html')

# View for API Data Page
def api_data_view(request):
    return render(request, 'dashboard/api_data.html', {
        'message': 'This is a placeholder for API data view.'
    })

# View for Live Tracking Page
def live_tracking(request):
    try:
        current_page = int(request.GET.get("page", 1))
    except ValueError:
        current_page = 1

    per_page = 10
    offset = (current_page - 1) * per_page

    staff_data = fetch_staff_data(offset, per_page)
    total_count = staff_data['total']
    items = staff_data['items']

    max_page = (total_count + per_page - 1) // per_page

    def get_pagination_range(current_page, max_page, delta=2):
        left = max(current_page - delta, 1)
        right = min(current_page + delta, max_page)
        range_pages = []

        if left > 1:
            range_pages.append(1)
            if left > 2:
                range_pages.append("...")

        range_pages.extend(range(left, right + 1))

        if right < max_page:
            if right < max_page - 1:
                range_pages.append("...")
            range_pages.append(max_page)

        return range_pages

    pagination_range = get_pagination_range(current_page, max_page)

    return render(request, 'dashboard/live_tracking.html', {
        'staff_data': items,
        'current_page': current_page,
        'previous_page': current_page - 1 if current_page > 1 else None,
        'next_page': current_page + 1 if (offset + per_page) < total_count else None,
        'pages': range(1, max_page + 1),
        'pagination_range': pagination_range,
        'max_page': max_page
    })

# Shared data fetch function

def fetch_staff_data(offset=0, limit=10):
    TIMESHEET_API = "https://crm.deluxebilisim.com/api/timesheets/"
    TASK_API = "https://crm.deluxebilisim.com/api/tasks/search/"
    PROJECT_API = "https://crm.deluxebilisim.com/api/projects/search/"
    STAFF_API = "https://crm.deluxebilisim.com/api/staffs/"
    HEADERS = {
        'authtoken': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGVsdXhldGltZSIsIm5hbWUiOiJkZWx1eGV0aW1lIiwiQVBJX1RJTUUiOjE3NDUzNDQyNjJ9.kJGo5DksaPwkHwufDvLMGaMmjk5q2F7GhjzwdHtfT_o'
    }

    BASE_DIR = Path(__file__).resolve().parent.parent

    try:
        res = requests.get(TIMESHEET_API, headers=HEADERS, timeout=10)
        res.raise_for_status()
        timesheets = res.json()
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
                "email": "",
                "screenshot_url": ""
            }

            try:
                task_id = item.get("task_id")
                project_id = item.get("project_id")
                staff_id = item.get("staff_id")
                start_time_str = item.get("start_time")
                end_time_str = item.get("end_time")

                if task_id:
                    task_res = requests.get(f"{TASK_API}{task_id}", headers=HEADERS, timeout=5)
                    task_data = task_res.json()
                    if isinstance(task_data, list) and task_data:
                        result['task_name'] = task_data[0].get("name", "N/A")
                    elif isinstance(task_data, dict):
                        result['task_name'] = task_data.get("name", "N/A")

                if project_id:
                    project_res = requests.get(f"{PROJECT_API}{project_id}", headers=HEADERS, timeout=5)
                    project_data = project_res.json()
                    if isinstance(project_data, list) and project_data:
                        result['project_name'] = project_data[0].get("name", "N/A")
                    elif isinstance(project_data, dict):
                        result['project_name'] = project_data.get("name", "N/A")

                if staff_id:
                    staff_res = requests.get(f"{STAFF_API}{staff_id}", headers=HEADERS, timeout=5)
                    staff_data = staff_res.json()
                    first = staff_data.get('firstname', '')
                    last = staff_data.get('lastname', '')
                    result['username'] = f"{first} {last}".strip() if first or last else "N/A"
                    result['job_position'] = staff_data.get("job_position", "N/A")
                    result['last_login'] = staff_data.get("last_login", "N/A")
                    profile_image = staff_data.get("profile_image", "")
                    result['email'] = staff_data.get("email", "")
                    if profile_image:
                        result['profile_image_url'] = f"https://crm.deluxebilisim.com/uploads/staff_profile_images/{staff_id}/small_{profile_image}"

                # Screenshot logic
                email = result.get("email", "").strip()
                task_name = result.get("task_name", "").strip()

                screenshot_dir = os.path.join(BASE_DIR, 'dashboard', 'static', 'screenshots', email, task_name)
                print(f"[🧪] Checking screenshot folder: {screenshot_dir}")

                if os.path.exists(screenshot_dir):
                    image_files = sorted([
                        f for f in os.listdir(screenshot_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                    ])
                    if image_files:
                        selected_image = image_files[0]
                        screenshot_url = f"screenshots/{quote(email)}/{quote(task_name)}/{quote(selected_image)}"
                        result['screenshot_url'] = screenshot_url
                        print(f"[✅] Screenshot URL: /static/{screenshot_url}")
                        print(f"[🖼️] Screenshot Full Path: {os.path.join(screenshot_dir, selected_image)}")
                    else:
                        print("[🚫] No image files found.")
                else:
                    print(f"[❌] Screenshot folder does NOT exist: {screenshot_dir}")

                if start_time_str and end_time_str:
                    start_dt = datetime.fromtimestamp(int(start_time_str))
                    end_dt = datetime.fromtimestamp(int(end_time_str))
                    result['total_spent_time'] = round((end_dt - start_dt).total_seconds() / 60, 2)

            except Exception as e:
                print(f"[❌] Error fetching details: {e}")

            return result

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(fetch_details, timesheets))

        return {"items": results, "total": total_count}

    except requests.RequestException as e:
        print(f"[❌] API Request Error: {e}")
        return {"items": [], "total": 0}
