from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from DSTBundesliga import views

admin.autodiscover()

urlpatterns = [
    path('', include(('DSTBundesliga.apps.dstffbl.urls', 'dstffbl'), namespace='dstffbl')),
    path('auth/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('leagues/', include('DSTBundesliga.apps.leagues.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('admin/', admin.site.urls),
    url(r'^shared/', include('filer.urls')),
    path('regelwerk/', views.regelwerk),
    re_path(r'^', include('cms.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
