import requests
from django.shortcuts import render
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dashboard.tasks import perform_search_and_cache
import time
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import quote
import os
from pathlib import Path
from dashboard.utils import fetch_staff_data
from .ai_helpers import normalize_task_name_with_ai, get_all_screenshot_paths

from .ai_search_helpers import ai_fuzzy_match_employees, generate_user_timeline_data
from dashboard.utils import fetch_all_employees
from django.views.decorators.http import require_GET
from dashboard.ai_search_helpers import get_user_timelines_by_staffid
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout

AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGVsdXhldGltZSIsIm5hbWUiOiJkZWx1eGV0aW1lIiwiQVBJX1RJTUUiOjE3NDUzNDQyNjJ9.kJGo5DksaPwkHwufDvLMGaMmjk5q2F7GhjzwdHtfT_o"
API_URL = "https://crm.deluxebilisim.com/api/staffs/"
BASE_DIR = Path(__file__).resolve().parent.parent

# def login_view(request):
#     return render(request, 'dashboard/login.html')

from django.contrib.auth.decorators import login_required



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # ✅ correct name

    error = None
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')  # ✅ correct name
        else:
            error = "Invalid username or password."

    return render(request, 'dashboard/login.html', {'error': error})



def logout_view(request):
    logout(request)
    return redirect('login')




@login_required
def index(request):
    return render(request, 'dashboard/index.html')


@login_required
def home(request):
    return render(request, 'dashboard/home.html')

def search_view(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "Search query cannot be empty."}, status=400)
    task = perform_search_and_cache.delay(query)
    return JsonResponse({"task_id": task.id, "status": "Task started"})

def search_status_view(request, task_id):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    if result.state == 'PENDING':
        return JsonResponse({"status": "Pending"})
    elif result.state == 'SUCCESS':
        return JsonResponse({"status": "Success", "data": result.result})
    elif result.state == 'FAILURE':
        return JsonResponse({"status": "Failure", "error": str(result.info)})
    else:
        return JsonResponse({"status": result.state})

def api_data_view(request):
    return render(request, 'dashboard/api_data.html', {
        'message': 'This is a placeholder for API data view.'
    })




@login_required
def live_tracking(request):
    print("✅ live_tracking view accessed")

    def format_minutes_or_hours(minutes):
        if minutes < 1:
            return f"{round(minutes * 60)}s"
        elif minutes < 60:
            return f"{round(minutes)}m"
        elif minutes % 60 == 0:
            return f"{int(minutes // 60)}h"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"

    search_query = request.GET.get("search", "").strip().lower()
    days_filter = request.GET.get("days", "").strip()

    try:
        current_page = int(request.GET.get("page", 1))
    except ValueError:
        current_page = 1

    per_page = 8
    offset = (current_page - 1) * per_page

    staff_data = fetch_staff_data(offset, per_page, search_query, days_filter)

    for row in staff_data['items']:
        time_spent = row.get("total_spent_time", 0)
        row["formatted_time"] = format_minutes_or_hours(time_spent)

        last_update = row.get("last_update_full")
        try:
            parsed = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - parsed).days >= 1:
                row["last_update_ago"] = parsed.strftime("%d %b %Y at %I:%M %p")
            else:
                row["last_update_ago"] = parsed.strftime("%I:%M %p")
        except Exception:
            row["last_update_ago"] = "Unknown"













        email = row.get("email", "")
        task = row.get("task_name", "")
        safe_task = normalize_task_name_with_ai(task)
        normalized_task_folder = os.path.join(BASE_DIR, 'dashboard', 'media', 'screenshots', email, safe_task)

        if os.path.exists(normalized_task_folder):
            image_files = sorted(
                [f for f in os.listdir(normalized_task_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
                key=lambda f: os.path.getmtime(os.path.join(normalized_task_folder, f)),
                reverse=True
            )
            if image_files:
                image_file = image_files[0]
                row["screenshot_url"] = f"/media/screenshots/{quote(email)}/{quote(safe_task)}/{quote(image_file)}"
                row["screenshot_name"] = image_file
            else:
                row["screenshot_url"] = ""
                row["screenshot_name"] = ""
        else:
            row["screenshot_url"] = ""
            row["screenshot_name"] = ""
            

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
        'max_page': max_page,
        'search_query': request.GET.get("search", ""),
        'days_filter': days_filter
    })





















































@login_required
def dashboard_view(request):
    from dashboard.ai_search_helpers import get_dashboard_context
    context = get_dashboard_context()

    screenshots = context.get('screenshots', [])
    latest = []

    for shot in screenshots:
        if shot.get("url"):
            latest.append({
                "url": shot["url"],
                "time": shot.get("time", ""),
                "user": shot.get("user", "Unknown"),
                "task": shot.get("task", "Untitled")
            })

    # Sort or slice if needed (assuming they're already sorted newest-first)
    context['latest_screenshots'] = latest[:5]

    return render(request, 'dashboard/index.html', context)














def search_employee_names(request):
    query = request.GET.get("q", "").strip().lower()

    try:
        res = requests.get(API_URL, headers={
            "authtoken": AUTH_TOKEN,
            "Accept": "application/json"
        }, timeout=10)
        res.raise_for_status()
        staff_list = res.json()

        cleaned = []
        for staff in staff_list:
            firstname = (staff.get("firstname") or "").strip()
            lastname = (staff.get("lastname") or "").strip()
            job = str(staff.get("job_position") or "").strip()
            full_name = f"{firstname} {lastname}".strip()
            if full_name:
                entry = {
                    "name": full_name,
                    "job": job,
                    "last_login": staff.get("last_login") or "1970-01-01 00:00:00"
                }
                cleaned.append(entry)

        if query:
            matches = [
                f"{emp['name']} – {emp['job']}"
                for emp in cleaned
                if query in emp['name'].lower()
            ]
        else:
            sorted_employees = sorted(
                cleaned,
                key=lambda x: x['last_login'],
                reverse=True
            )
            matches = [
                f"{emp['name']} – {emp['job']}"
                for emp in sorted_employees[:10]
            ]

        return JsonResponse({"matches": matches})

    except Exception as e:
        print(f"[❌ search_employee_names] Error: {e}")
        return JsonResponse({"matches": []})





@require_GET
def user_timeline_view(request):
    staffid = request.GET.get("staffid")
    if not staffid:
        return JsonResponse({"error": "Missing staffid parameter"}, status=400)

    try:
        timeline_entries = get_user_timelines_by_staffid(staffid)
        return JsonResponse({"entries": timeline_entries}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from .ai_helpers import get_all_screenshot_paths

@login_required
def live_tracking_view(request):
    print("✅ live_tracking view accessed")
    staff_data = [...]  # Fetch staff data from your database or API
    screenshot_map = get_all_screenshot_paths()

    # Add screenshot URLs to staff_data
    for staff in staff_data:
        email = staff['email'].lower()
        task_name = staff['task_name'].lower()
        key = (email, task_name)
        staff['screenshots'] = screenshot_map.get(key, [])

    return render(request, 'dashboard/live_tracking.html', {'staff_data': staff_data})