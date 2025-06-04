<<<<<<< HEAD
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DDS.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
=======
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DDS.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
>>>>>>> e5c64bf8a42282904ea76d2726122b8d9fb227af
