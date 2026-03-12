from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('admin-panel/', include('adminapp.urls')),
]

# ഈ ഭാഗം കൃത്യമായി ഉണ്ടെന്ന് ഉറപ്പാക്കുക
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)