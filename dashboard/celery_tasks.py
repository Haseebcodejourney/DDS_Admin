from celery import shared_task
from dashboard.utils import fetch_staff_data



@shared_task(bind=True)
def perform_search_and_cache(self, query, offset=0, limit=50):
    import logging
    logger = logging.getLogger('celery')
    logger.info(f"[📥 CELERY RECEIVED] Query: {query}")
    print(f"[🔍 CELERY] Task started for query: '{query}'")
    try:
        print(f"[🔍 CELERY] Task started for query: '{query}', offset: {offset}, limit: {limit}")
        
        results = fetch_staff_data(offset=offset, limit=limit, search_query=query)

        print(f"[✅ CELERY] Fetched {len(results['items'])} items for query: '{query}'")

        return results['items']
    
    except Exception as e:
        print(f"[❌ CELERY ERROR] {str(e)}")
        self.retry(exc=e, countdown=10, max_retries=3)  # Optional retry logic
        return {"error": str(e)}
