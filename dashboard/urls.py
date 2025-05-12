from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('index/', views.dashboard_view, name='dashboard'),
    # path('index/', views.home, name='index'),
    path('live/', views.live_tracking, name='live_tracking'),
    path('api-data/', views.api_data_view, name='api_data'),
    path('search-employee-names/', views.search_employee_names, name='search_employee_names'),
    path('api/user-timeline/', views.user_timeline_view, name='user_timeline'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
