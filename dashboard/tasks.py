import time
from celery import shared_task
from dashboard.utils import fetch_staff_data

@shared_task
def perform_search_and_cache(query, offset=0, limit=10):
    print(f"[🔍] Celery task started for query: {query}")
    start = time.time()
    
    result = fetch_staff_data(offset=offset, limit=limit, search_query=query)
    
    duration = time.time() - start
    print(f"[✅] Finished in {round(duration, 2)}s - {len(result['items'])} results")
    
    return result
