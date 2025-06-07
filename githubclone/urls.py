from django.contrib import admin
from django.urls import path, include  # <-- ¡Aquí se importa `path`!
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('projects.urls')),  # <-- tu app principal
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
