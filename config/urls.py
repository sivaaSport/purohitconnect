from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # App URLs will be included here as they are created
    path('', include('apps.core.urls')),
    path('api/v1/', include('apps.api.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('purohits/', include('apps.purohits.urls')),
    path('pujas/', include('apps.pujas.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
