# dashboard/ai_search_helpers.py
import openai
from difflib import get_close_matches
from django.conf import settings
import requests
from datetime import datetime
from datetime import datetime, timedelta

# Load from Django settings
openai.api_key = getattr(settings, "OPENAI_API_KEY", None)

try:
    from rapidfuzz import process, fuzz
    USE_RAPIDFUZZ = True
except ImportError:
    USE_RAPIDFUZZ = False
    print("[⚠️ Warning] rapidfuzz not installed. Falling back to difflib.")

# CRM Configuration
CRM_HEADERS = {
    "authtoken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGVsdXhldGltZSIsIm5hbWUiOiJkZWx1eGV0aW1lIiwiQVBJX1RJTUUiOjE3NDUzNDQyNjJ9.kJGo5DksaPwkHwufDvLMGaMmjk5q2F7GhjzwdHtfT_o"
}
CRM_BASE = "https://crm.deluxebilisim.com/api"

# --- AI Matching Helpers ---
def ai_normalize_name(name):
    try:
        prompt = f"Normalize the following person name for better search matching:\n\nName: {name}\nNormalized:"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=10,
            temperature=0.2
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"[AI Error] {e}")
        return name

def ai_fuzzy_match_employees(query, all_names, limit=10):
    try:
        normalized_query = ai_normalize_name(query)
        return get_close_matches(normalized_query, all_names, n=limit, cutoff=0.5)
    except Exception as e:
        print(f"[Fuzzy Match Error] {e}")
        return []

# --- AI Activity Classification ---
def classify_duration(minutes, task_name):
    try:
        prompt = (
            f"Is spending {minutes} minutes on the task '{task_name}' considered good productivity?\n"
            f"Answer only with one of: Good, Normal, No Good."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Duration Error] {e}")
        return "Unknown"

def classify_activity(title, details):
    try:
        prompt = (
            f"Given the title '{title}' and details '{details}', classify the employee's activity as one of: Working, Idle, Break, Meeting."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Activity Error] {e}")
        return "Unknown"

# --- CRM Fetch Helpers ---
def fetch_task_details(task_id):
    try:
        res = requests.get(f"{CRM_BASE}/tasks/search/{task_id}", headers=CRM_HEADERS)
        res.raise_for_status()
        data = res.json()
        return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"[❌ fetch_task_details] {e}")
        return {}

def fetch_project_details(project_id):
    try:
        res = requests.get(f"{CRM_BASE}/projects/search/{project_id}", headers=CRM_HEADERS)
        res.raise_for_status()
        data = res.json()
        return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"[❌ fetch_project_details] {e}")
        return {}

def compute_duration_minutes(start, end):
    try:
        start_dt = datetime.fromtimestamp(int(start))
        end_dt = datetime.fromtimestamp(int(end))
        duration = (end_dt - start_dt).total_seconds() / 60
        return round(duration, 2), start_dt.strftime("%I:%M %p")
    except Exception as e:
        print(f"[❌ compute_duration_minutes] {e}")
        return 0, "Unknown"

def evaluate_productivity_score(duration):
    if duration >= 60:
        return "Good"
    elif 30 <= duration < 60:
        return "Normal"
    else:
        return "Needs Attention"

def classify_task_activity(task_name):
    keywords = task_name.lower()
    if any(word in keywords for word in ["zoom", "meet", "call"]):
        return "Meeting"
    elif any(word in keywords for word in ["break", "pause", "rest"]):
        return "Idle"
    else:
        return "Working"

def enrich_timeline_entry(entry):
    task_id = entry.get("task_id")
    project_id = entry.get("project_id")
    start = entry.get("start_time")
    end = entry.get("end_time")

    task_data = fetch_task_details(task_id) if task_id else {}
    project_data = fetch_project_details(project_id) if project_id else {}

    duration_min, start_str = compute_duration_minutes(start, end)

    return {
        "time": start_str,
        "title": project_data.get("name", "Unknown Project"),
        "details": task_data.get("name", "Unknown Task"),
        "duration": f"{int(duration_min)}m" if duration_min < 60 else f"{int(duration_min // 60)}h {int(duration_min % 60)}m",
        "switches": entry.get("switch_count", 0),
        "score": evaluate_productivity_score(duration_min),
        "activity": classify_task_activity(task_data.get("name", ""))
    }

def enrich_all_timeline_entries(entries):
    return [enrich_timeline_entry(e) for e in entries]

def timestamp_to_clock(timestamp):
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "Invalid"
    else:
        return "Invalid"
    return dt.strftime("%-I:%M %p")

def analyze_employee_focus(timesheet, task, project):
    duration_min = round((timesheet["end_time"] - timesheet["start_time"]) / 60, 2)
    score = "Good" if duration_min > 45 else "Normal" if duration_min > 20 else "No Good"
    activity = "Working" if duration_min > 0 else "Idle"
    return {
        "start_time": timestamp_to_clock(timesheet["start_time"]),
        "duration": f"{int(duration_min)}m",
        "project": project.get("name", "N/A"),
        "task": task.get("name", "N/A"),
        "score": score,
        "activity": activity,
    }


def generate_user_timeline_data(timesheet_entry):
    """
    Given a timesheet entry, fetch and compute all enriched data for timeline UI.
    """
    task_id = timesheet_entry.get("task_id")  # ✅ expects dict
    project_id = timesheet_entry.get("project_id")

    task = fetch_task_details(task_id) if task_id else {}
    project = fetch_project_details(project_id) if project_id else {}

    return analyze_employee_focus(timesheet_entry, task, project)


def get_dashboard_context():
    now = datetime.now()

    status_counts = {
        'at_work': 5,
        'in_meeting': 2,
        'at_break': 1,
        'idle': 0,
        'off': 3,
    }

    company_avg = {
        'breaks_per_day': 2.1,
        'avg_break_duration': 12.6,
        'meetings_per_day': 1.7,
        'avg_meeting_duration': 18.2,
        'spread': {
            'work': 76,
            'meeting': 10,
            'break': 9,
            'idle': 5,
        }
    }

    screenshots = [
        {'url': '/media/screenshots/screen_1.jpg', 'time': '1:13 PM'},
        {'url': '/media/screenshots/screen_2.jpg', 'time': '1:12 PM'},
        {'url': '/media/screenshots/screen_3.jpg', 'time': '1:11 PM'},
        {'url': '/media/screenshots/screen_4.jpg', 'time': '1:10 PM'},
    ]

    employees = [
        "Hamza Haseeb – 188",
        "John Smith – 177",
        "Emily Rose – 153",
        "Diana Adams – 121",
    ]

    timeline_stats = {
        'total_switches': 265,
        'total_duration': "2h 18m"
    }

    timeline_entries = [
        {
            'time': "1:10 PM",
            'project': "FocusPro",
            'task': "CRM Dashboard Fix",
            'duration': "1h 12m",
            'score': "Good",
            'activity_type': "Working"
        },
        {
            'time': "12:30 PM",
            'project': "Zoom Call",
            'task': "Client Presentation",
            'duration': "32m",
            'score': "Normal",
            'activity_type': "Meeting"
        }
    ]

    available_dates = [(now - timedelta(days=i)).strftime("%d %b %Y") for i in range(3)]
    selected_date = available_dates[0]

    return {
        'status_counts': status_counts,
        'company_avg': company_avg,
        'screenshots': screenshots,
        'employees': employees,
        'timeline_stats': timeline_stats,
        'timeline_entries': timeline_entries,
        'available_dates': available_dates,
        'selected_date': selected_date,
        'current_date': now.strftime('%d/%m/%Y')
    }


def get_user_timelines_by_staffid(staffid):
    try:
        res = requests.get(f"{CRM_BASE}/timesheets/", headers=CRM_HEADERS)
        res.raise_for_status()
        all_timesheets = res.json()

        user_entries = [ts for ts in all_timesheets if str(ts.get("staff_id")) == str(staffid)]

        enriched = [generate_user_timeline_data(entry) for entry in user_entries]
        return enriched
    except Exception as e:
        print(f"[❌ get_user_timelines_by_staffid] {e}")
        return []
