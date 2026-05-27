from django.contrib import admin
from django.urls import path, include  # Импортируйте include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Мы говорим проекту: "Все ссылки, которые начинаются с пустого места,
    # ищи в файле catalog/urls.py"
    path('', include('catalog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)