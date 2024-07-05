from django.contrib import admin
from django.urls import path
from . views import query_claude
from . views import view_logs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', query_claude, name='query_claude'),
    path('logs/', view_logs, name='view_logs'),
]


